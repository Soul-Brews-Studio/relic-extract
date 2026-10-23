//! `run` and `status`: which months of which streams to cut, and OUT/<stream>/_extract.json.
//!
//! A month is cut again when its source is newer than the part, or when the stream's settings changed
//! (_extract.json keeps their hash; the same hash as the Python version, so its parts stay fresh).

use std::fs;
use std::path::Path;

use serde_json::{Value, json};

use crate::config::{self, Config};
use crate::extract::{self, Done};

/// json.dumps(v, indent=1) layout (non-ASCII is written as is, not escaped).
pub fn pretty(v: &Value) -> String {
    let mut buf = Vec::new();
    let fmt = serde_json::ser::PrettyFormatter::with_indent(b" ");
    let mut ser = serde_json::Serializer::with_formatter(&mut buf, fmt);
    serde::Serialize::serialize(v, &mut ser).unwrap();
    String::from_utf8(buf).unwrap()
}

fn mtime(p: &Path) -> Option<std::time::SystemTime> {
    fs::metadata(p).and_then(|m| m.modified()).ok()
}

/// Cut every enabled stream's months that need it. `months`: only these; `force`: cut them all.
pub fn run(cfg: &Config, months: Option<Vec<String>>, force: bool, only: Option<&str>) -> Result<Vec<Done>, String> {
    let src = extract::months_in(cfg.source());
    if src.is_empty() {
        return Err(format!("no month files in {}\n  relic-scan run   (or set [extract] source)", cfg.source()));
    }
    // "changed" | "all" | a list
    let want: Option<Vec<String>> = match months {
        Some(mut m) => {
            m.sort();
            Some(m)
        }
        None => cfg.v["months"].as_array().map(|a| a.iter().filter_map(|x| x.as_str().map(str::to_string)).collect()),
    };
    let changed_only = want.is_none() && cfg.v["months"] == "changed";
    if let Some(w) = &want {
        let missing: Vec<&str> = w.iter().filter(|m| !src.contains_key(*m)).map(String::as_str).collect();
        if !missing.is_empty() {
            return Err(format!("no source for month(s) {} in {}", missing.join(", "), cfg.source()));
        }
    }
    if let Some(s) = only
        && !config::STREAMS.contains(&s) {
        return Err(format!("unknown stream {s} (known: {})", config::STREAMS.join(", ")));
    }
    let sess = extract::sessions(cfg.source());
    let mut done = vec![];
    for name in config::STREAMS {
        let st = cfg.stream(name);
        if st["enabled"] != true || only.is_some_and(|s| s != name) {
            continue;
        }
        let sdir = Path::new(cfg.out()).join(name);
        let state_f = sdir.join("_extract.json");
        let state: Value = fs::read(&state_f).ok().and_then(|b| serde_json::from_slice(&b).ok()).unwrap_or(json!({}));
        let h = cfg.stream_hash(name);
        let stale = state["hash"].as_str() != Some(h.as_str());
        if stale && state.as_object().is_some_and(|m| !m.is_empty()) {
            eprintln!("extract {name}: settings changed since the last run, every month is cut again");
        }
        let before = done.len();
        for (m, f) in &src {
            if want.as_ref().is_some_and(|w| !w.contains(m)) {
                continue;
            }
            let out = sdir.join(format!("{m}.parquet"));
            let fresh = matches!((mtime(&out), mtime(f)), (Some(o), Some(s)) if o >= s);
            if changed_only && fresh && !stale && !force {
                continue;
            }
            done.push(extract::cut_month(cfg, name, m, f, &out, &sess)?);
        }
        // a stale stream cut for a few months only keeps its old hash, so the rest are cut on the next full run
        if !(stale && want.is_some()) {
            config::private_dir(&sdir).map_err(|e| e.to_string())?;
            let at = chrono::Local::now().format("%Y-%m-%dT%H:%M:%S%z").to_string();
            let body = json!({"hash": h, "settings": {"stream": st, "dedupe": cfg.v["dedupe"], "chunk": cfg.v["chunk"]},
                              "source": cfg.source(), "at": at});
            let tmp = sdir.join("_extract.json.part");
            fs::write(&tmp, pretty(&body)).map_err(|e| e.to_string())?;
            fs::rename(&tmp, &state_f).map_err(|e| e.to_string())?;
        }
        eprintln!("extract {name}: {} month(s) cut -> {}", done.len() - before, sdir.display());
    }
    Ok(done)
}

pub fn status(cfg: &Config) {
    for name in config::STREAMS {
        let on = if cfg.stream(name)["enabled"] == true { "on " } else { "off" };
        let d = Path::new(cfg.out()).join(name);
        let mut parts: Vec<_> = fs::read_dir(&d).into_iter().flatten().flatten().map(|e| e.path())
            .filter(|p| p.extension().is_some_and(|x| x == "parquet")).collect();
        parts.sort();
        if parts.is_empty() {
            println!("{name:9} {on}  no parts");
            continue;
        }
        let (n, u, last) = crate::read::part_stats(&parts);
        println!("{name:9} {on}  {} months · {} chunks · {} distinct texts · newest {}", parts.len(), extract::num(n),
                 extract::num(u), last.unwrap_or_default());
    }
}
