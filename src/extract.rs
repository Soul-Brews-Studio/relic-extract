//! relic-scan month files -> OUT/<stream>/YYYY-MM.parquet, one row per chunk to embed.
//!
//! Same cut and keys as agent-relic-v4 split.py (recipe text-v1) and jsonl-truth embed/export.py, so a chunk's key
//! finds a vector already embedded by either. The Python relic-extract (src/relic_extract) is the reference;
//! `just parity` compares the two on every month.
//!
//! Per stream (text, thinking, tools; each on or off in [extract.streams.*]):
//!   rows      s = <stream>, the field not empty after trimming spaces (tools: kind in kinds)
//!   dedupe    "content": one row per msgkey, the smallest (h, idx) kept, n_h = rows holding it · "h": one per (h, idx)
//!   cut       text/thinking: max_chars with overlap, in characters (chunk = 0, 1, …) · tools: body cut at max_chars
//!   cat/probe from meta/sessions.parquet (tier = main), by sid; '(no session)' / false when there is none
//!   order     ts, msgkey (then h, idx)

use std::collections::HashMap;
use std::fs;
use std::path::Path;
use std::sync::Arc;
use std::time::Instant;

use arrow::array::{Array, ArrayRef, BooleanBuilder, Int64Builder, RecordBatch, StringBuilder};
use arrow::datatypes::{DataType, Field, Schema};
use md5::{Digest, Md5};
use parquet::arrow::ArrowWriter;
use parquet::basic::{Compression, ZstdLevel};
use parquet::file::properties::WriterProperties;

use crate::config::{self, Config};
use crate::read::{self, Cols};

pub const NAMES: [&str; 17] = ["key", "msgkey", "chunk", "h", "n_h", "month", "sid", "ts", "ts_th", "engine", "role", "type",
                               "kind", "name", "cat", "probe", "text"];

/// Same cut as jsonl-truth embed/export.py and relic4 split.py: characters (code points), not bytes.
pub fn chunks(text: &str, max_chars: usize, overlap: usize) -> Vec<&str> {
    let starts: Vec<usize> = text.char_indices().map(|(i, _)| i).collect();
    let n = starts.len();
    if n <= max_chars {
        return vec![text];
    }
    let at = |c: usize| if c >= n { text.len() } else { starts[c] };
    let (mut out, mut i, step) = (vec![], 0, max_chars - overlap);
    while i < n {
        out.push(&text[at(i)..at(i + max_chars)]);
        i += step;
    }
    out
}

/// The first `max` characters.
pub fn clip(text: &str, max: usize) -> &str {
    match text.char_indices().nth(max) {
        Some((i, _)) => &text[..i],
        None => text,
    }
}

/// blake2b-128 of the chunk text, hex: the embedding cache key.
pub fn key(t: &str) -> String {
    blake2b_simd::Params::new().hash_length(16).hash(t.as_bytes()).to_hex().to_string()
}

fn md5_hex(s: &str) -> String {
    let d = Md5::digest(s.as_bytes());
    d.iter().map(|b| format!("{b:02x}")).collect()
}

/// agent-relic-v4 src/relic4/sql.py MSGKEY — keep byte-identical: relic4 and relic-embed key on it.
pub fn msgkey(c: &Cols, i: usize) -> String {
    let s = c.s.get(i);
    if s == Some("tools") {
        let idx = c.idx.value(i).to_string();
        let err = c.err.as_ref().and_then(|e| (!e.is_null(i)).then(|| if e.value(i) { "true" } else { "false" }));
        md5_hex(&crate::json::duckdb_list(&[s, c.ts.get(i), Some(&idx), c.kind.get(i), c.call_id.get(i), c.name.get(i),
                                            c.body.get(i), err]))
    } else {
        md5_hex(&crate::json::duckdb_list(&[s, c.role.get(i), c.ts.get(i), c.text.get(i)]))
    }
}

/// {month: path} for every month file relic-scan wrote (YYYY-MM.parquet, undated.parquet), sorted.
pub fn months_in(source: &str) -> std::collections::BTreeMap<String, std::path::PathBuf> {
    let mut out = std::collections::BTreeMap::new();
    for e in fs::read_dir(source).into_iter().flatten().flatten() {
        let n = e.file_name().to_string_lossy().to_string();
        let Some(m) = n.strip_suffix(".parquet") else { continue };
        let b = m.as_bytes();
        let ok = m == "undated"
            || (b.len() == 7 && b[4] == b'-' && b.iter().enumerate().all(|(i, c)| i == 4 || c.is_ascii_digit()));
        if ok && e.path().is_file() {
            out.insert(m.to_string(), e.path());
        }
    }
    out
}

/// sid -> (cat, probe) from meta/sessions.parquet, main tier only (any_value(cat) = the first non-null, bool_or(probe)).
pub fn sessions(source: &str) -> HashMap<String, (Option<String>, Option<bool>)> {
    let mut m: HashMap<String, (Option<String>, Option<bool>)> = HashMap::new();
    let p = Path::new(source).join("meta").join("sessions.parquet");
    if !p.exists() {
        return m;
    }
    for (sid, tier, cat, probe) in read::sessions(&p) {
        if tier.as_deref() != Some("main") {
            continue;
        }
        let Some(sid) = sid else { continue };
        let e = m.entry(sid).or_default();
        if e.0.is_none() {
            e.0 = cat;
        }
        e.1 = match (e.1, probe) {
            (Some(a), Some(b)) => Some(a || b),
            (a, b) => a.or(b),
        };
    }
    m
}

struct Pick {
    row: (usize, usize), // (batch, row) of the kept copy
    hidx: (i64, i64),
    n: i64,
    msgkey: String,
}

pub struct Done {
    pub messages: usize,
    pub chunks: usize,
    pub distinct: usize,
}

pub fn cut_month(cfg: &Config, name: &str, month: &str, src: &Path, out: &Path,
                 sess: &HashMap<String, (Option<String>, Option<bool>)>) -> Result<Done, String> {
    let t0 = Instant::now();
    let st = cfg.stream(name);
    let field = st["field"].as_str().unwrap_or("text");
    let kinds: Vec<String> = st["kinds"].as_array().map(|a| a.iter().filter_map(|k| k.as_str().map(str::to_string)).collect())
        .unwrap_or_else(|| vec!["call".into()]);
    let batches = read::month(src, field).map_err(|e| format!("{}: {e}", src.display()))?;
    let content = cfg.content_dedupe();
    // dedupe: one Pick per partition (msgkey, or (h, idx)), the smallest (h, idx) kept
    let mut picks: HashMap<String, Pick> = HashMap::new();
    for (bi, c) in batches.iter().enumerate() {
        for i in 0..c.len {
            if c.s.get(i) != Some(name) {
                continue;
            }
            let Some(body) = c.field.get(i) else { continue };
            if body.trim_matches(' ').is_empty() {
                continue;
            }
            if name == "tools" && !c.kind.get(i).is_some_and(|k| kinds.iter().any(|x| x == k)) {
                continue;
            }
            let mk = msgkey(c, i);
            let hidx = (c.h.value(i), c.idx.value(i));
            let part = if content { mk.clone() } else { format!("{}:{}", hidx.0, hidx.1) };
            let p = picks.entry(part).or_insert(Pick { row: (bi, i), hidx, n: 0, msgkey: mk });
            p.n += 1;
            if hidx < p.hidx {
                p.hidx = hidx;
                p.row = (bi, i);
            }
        }
    }
    let mut kept: Vec<&Pick> = picks.values().collect();
    kept.sort_by(|a, b| {
        let ta = batches[a.row.0].ts.get(a.row.1);
        let tb = batches[b.row.0].ts.get(b.row.1);
        (ta.is_none(), ta, &a.msgkey, a.hidx).cmp(&(tb.is_none(), tb, &b.msgkey, b.hidx))
    });
    let (mc, ov) = (cfg.max_chars(), cfg.overlap());
    let tool_max = st["max_chars"].as_u64().unwrap_or(2000) as usize;
    let mut sb: Vec<StringBuilder> = (0..NAMES.len()).map(|_| StringBuilder::new()).collect();
    let (mut chunk_b, mut h_b, mut nh_b, mut probe_b) = (Int64Builder::new(), Int64Builder::new(), Int64Builder::new(),
                                                         BooleanBuilder::new());
    let mut keys = std::collections::HashSet::new();
    let mut n = 0usize;
    for p in &kept {
        let (c, i) = (&batches[p.row.0], p.row.1);
        let body = c.field.get(i).unwrap_or("");
        let pieces = if name == "tools" { vec![clip(body, tool_max)] } else { chunks(body, mc, ov) };
        let sid = c.sid.get(i);
        let (cat, probe) = sid.and_then(|s| sess.get(s)).cloned().unwrap_or((None, None));
        for (ci, piece) in pieces.into_iter().enumerate() {
            let k = key(piece);
            let vals: [Option<&str>; 17] = [Some(&k), Some(&p.msgkey), None, None, None, Some(month), sid, c.ts.get(i),
                c.ts_th.get(i), c.engine.get(i), c.role.get(i), c.typ.get(i), c.kind.get(i), c.name.get(i),
                Some(cat.as_deref().unwrap_or("(no session)")), None, Some(piece)];
            for (j, v) in vals.iter().enumerate() {
                if !matches!(NAMES[j], "chunk" | "h" | "n_h" | "probe") {
                    sb[j].append_option(*v);
                }
            }
            chunk_b.append_value(ci as i64);
            h_b.append_value(c.h.value(i));
            nh_b.append_value(p.n);
            probe_b.append_value(probe.unwrap_or(false));
            keys.insert(k);
            n += 1;
        }
    }
    let mut cols: Vec<ArrayRef> = vec![];
    let mut fields = vec![];
    for (j, nm) in NAMES.iter().enumerate() {
        let (a, t): (ArrayRef, DataType) = match *nm {
            "chunk" => (Arc::new(chunk_b.finish()), DataType::Int64),
            "h" => (Arc::new(h_b.finish()), DataType::Int64),
            "n_h" => (Arc::new(nh_b.finish()), DataType::Int64),
            "probe" => (Arc::new(probe_b.finish()), DataType::Boolean),
            _ => (Arc::new(sb[j].finish()), DataType::Utf8),
        };
        cols.push(a);
        fields.push(Field::new(*nm, t, true));
    }
    let schema = Arc::new(Schema::new(fields));
    let batch = RecordBatch::try_new(schema.clone(), cols).map_err(|e| e.to_string())?;
    write_atomic(out, schema, &batch)?;
    let d = Done { messages: kept.len(), chunks: n, distinct: keys.len() };
    eprintln!("extract {name} {month}: {} messages -> {} chunks ({} distinct texts) · {:.1}s", num(d.messages), num(d.chunks),
              num(d.distinct), t0.elapsed().as_secs_f64());
    Ok(d)
}

fn write_atomic(out: &Path, schema: Arc<Schema>, batch: &RecordBatch) -> Result<(), String> {
    if let Some(d) = out.parent() {
        config::private_dir(d).map_err(|e| e.to_string())?;
    }
    let tmp = out.with_extension("parquet.part");
    let props = WriterProperties::builder().set_compression(Compression::ZSTD(ZstdLevel::try_new(3).unwrap())).build();
    let f = fs::File::create(&tmp).map_err(|e| format!("{}: {e}", tmp.display()))?;
    let mut w = ArrowWriter::try_new(f, schema, Some(props)).map_err(|e| e.to_string())?;
    w.write(batch).map_err(|e| e.to_string())?;
    w.into_inner().map_err(|e| e.to_string())?.sync_all().map_err(|e| e.to_string())?;
    fs::rename(&tmp, out).map_err(|e| e.to_string())?;
    config::private_file(out).map_err(|e| e.to_string())
}

pub fn num(n: usize) -> String {
    let s = n.to_string();
    let mut out = String::new();
    for (i, c) in s.chars().enumerate() {
        if i > 0 && (s.len() - i) % 3 == 0 {
            out.push(',');
        }
        out.push(c);
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cut_like_relic4() {
        let t = "x".repeat(13000);
        let c = chunks(&t, 6000, 400);
        assert_eq!(c.iter().map(|p| p.len()).collect::<Vec<_>>(), vec![6000, 6000, 1800]);
        let th = "ก".repeat(6001); // 3 bytes a character: the cut counts characters
        assert_eq!(chunks(&th, 6000, 400).iter().map(|p| p.chars().count()).collect::<Vec<_>>(), vec![6000, 401]);
        assert_eq!(chunks("short", 6000, 400), vec!["short"]);
        assert_eq!(clip("ไทยไทย", 3), "ไทย");
    }

    #[test]
    fn key_is_blake2b_128() {
        // python: hashlib.blake2b(b"hello", digest_size=16).hexdigest()
        assert_eq!(key("hello"), "46fb7408d4f285228f4af516ea25851b");
    }

    #[test]
    fn md5_of_duckdb_json() {
        // duckdb: select md5(to_json(['text','user','2026-10-01T00:00:00Z','hello']))
        let j = crate::json::duckdb_list(&[Some("text"), Some("user"), Some("2026-10-01T00:00:00Z"), Some("hello")]);
        assert_eq!(md5_hex(&j), "2bcaccff2f6a357888f1a251c0863d99");
    }
}
