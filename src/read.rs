//! Reading relic-scan's Parquet: a month file (only the columns a stream needs) and meta/sessions.parquet.

use std::fs;
use std::path::Path;

use arrow::array::{Array, ArrayRef, AsArray, BooleanArray, Int64Array, RecordBatch};
use arrow::datatypes::DataType;
use parquet::arrow::ProjectionMask;
use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;

/// A string column, whatever Arrow string type the file holds; a missing column reads as all NULL.
#[derive(Clone)]
pub struct Str(Option<ArrayRef>);

impl Str {
    pub fn get(&self, i: usize) -> Option<&str> {
        let a = self.0.as_ref()?;
        if a.is_null(i) {
            return None;
        }
        Some(match a.data_type() {
            DataType::Utf8 => a.as_string::<i32>().value(i),
            DataType::LargeUtf8 => a.as_string::<i64>().value(i),
            DataType::Utf8View => a.as_string_view().value(i),
            _ => return None,
        })
    }
}

/// One batch of a month file, by column.
pub struct Cols {
    pub len: usize,
    pub s: Str,
    pub h: Int64Array,
    pub idx: Int64Array,
    pub engine: Str,
    pub role: Str,
    pub typ: Str,
    pub sid: Str,
    pub ts: Str,
    pub ts_th: Str,
    pub text: Str,
    pub kind: Str,
    pub call_id: Str,
    pub name: Str,
    pub body: Str,
    pub err: Option<BooleanArray>,
    pub field: Str, // the stream's field (text or body)
}

fn col(b: &RecordBatch, n: &str) -> Str {
    Str(b.column_by_name(n).cloned())
}

fn ints(b: &RecordBatch, n: &str) -> Result<Int64Array, String> {
    b.column_by_name(n).and_then(|a| a.as_any().downcast_ref::<Int64Array>().cloned()).ok_or(format!("no INT64 column {n}"))
}

/// Every batch of a month file. Reads only what msgkey, the filter and the output need.
pub fn month(path: &Path, field: &str) -> Result<Vec<Cols>, String> {
    let f = fs::File::open(path).map_err(|e| e.to_string())?;
    let b = ParquetRecordBatchReaderBuilder::try_new(f).map_err(|e| e.to_string())?;
    let want = ["s", "h", "idx", "engine", "role", "type", "sid", "ts", "ts_th", "text", "kind", "call_id", "name", "body", "err",
                field];
    let idx: Vec<usize> = want.iter().filter_map(|n| b.schema().index_of(n).ok()).collect();
    let mask = ProjectionMask::roots(b.parquet_schema(), idx);
    let rd = b.with_projection(mask).with_batch_size(32_768).build().map_err(|e| e.to_string())?;
    let mut out = vec![];
    for batch in rd {
        let b = batch.map_err(|e| e.to_string())?;
        out.push(Cols {
            len: b.num_rows(), s: col(&b, "s"), h: ints(&b, "h")?, idx: ints(&b, "idx")?, engine: col(&b, "engine"),
            role: col(&b, "role"), typ: col(&b, "type"), sid: col(&b, "sid"), ts: col(&b, "ts"), ts_th: col(&b, "ts_th"),
            text: col(&b, "text"), kind: col(&b, "kind"), call_id: col(&b, "call_id"), name: col(&b, "name"),
            body: col(&b, "body"), err: b.column_by_name("err").and_then(|a| a.as_any().downcast_ref::<BooleanArray>().cloned()),
            field: col(&b, field),
        });
    }
    Ok(out)
}

/// (sid, tier, cat, probe) per row of meta/sessions.parquet.
pub fn sessions(path: &Path) -> Vec<(Option<String>, Option<String>, Option<String>, Option<bool>)> {
    let mut out = vec![];
    let Ok(f) = fs::File::open(path) else { return out };
    let Ok(b) = ParquetRecordBatchReaderBuilder::try_new(f) else { return out };
    let Ok(rd) = b.build() else { return out };
    for batch in rd.flatten() {
        let (sid, tier, cat) = (col(&batch, "sid"), col(&batch, "tier"), col(&batch, "cat"));
        let probe = batch.column_by_name("probe").and_then(|a| a.as_any().downcast_ref::<BooleanArray>().cloned());
        for i in 0..batch.num_rows() {
            let p = probe.as_ref().and_then(|p| (!p.is_null(i)).then(|| p.value(i)));
            out.push((sid.get(i).map(str::to_string), tier.get(i).map(str::to_string), cat.get(i).map(str::to_string), p));
        }
    }
    out
}

/// (rows, distinct keys, newest ts) over the parts of a stream, for `status`.
pub fn part_stats(files: &[std::path::PathBuf]) -> (usize, usize, Option<String>) {
    let (mut n, mut keys, mut last): (usize, std::collections::HashSet<String>, Option<String>) = (0, Default::default(), None);
    for p in files {
        let Ok(f) = fs::File::open(p) else { continue };
        let Ok(b) = ParquetRecordBatchReaderBuilder::try_new(f) else { continue };
        let idx: Vec<usize> = ["key", "ts"].iter().filter_map(|c| b.schema().index_of(c).ok()).collect();
        let mask = ProjectionMask::roots(b.parquet_schema(), idx);
        let Ok(rd) = b.with_projection(mask).build() else { continue };
        for batch in rd.flatten() {
            let (k, t) = (col(&batch, "key"), col(&batch, "ts"));
            for i in 0..batch.num_rows() {
                n += 1;
                if let Some(x) = k.get(i) {
                    keys.insert(x.to_string());
                }
                if let Some(x) = t.get(i)
                    && last.as_deref().is_none_or(|l| x > l) {
                    last = Some(x.to_string());
                }
            }
        }
    }
    (n, keys.len(), last)
}
