//! ~/.arra/relic.toml: one file for the whole chain, one nested table per tool.
//!
//!   scan -> extract -> embed
//!   [scan]      relic-scan (today it still reads ~/.relic-scan/_config.json; reserved here)
//!   [extract]   this tool: which months and streams go in, how text is deduped and cut
//!   [embed]     relic-embed (next): model, gb300 / local runs, output
//!
//! ARRA_CONFIG overrides the path; --config overrides both. A missing file or key falls back to DEFAULTS, which are
//! jsonl-truth embed/workflow.toml's choices as of 2026-10-22 (text only, content dedupe, 6000/400 chunks).

use std::fs;
use std::os::unix::fs::{DirBuilderExt, PermissionsExt};
use std::path::{Path, PathBuf};

use serde_json::{Map, Value, json};

pub const STREAMS: [&str; 3] = ["text", "thinking", "tools"];

pub const TEMPLATE: &str = r##"# ~/.arra/relic.toml — the relic chain: scan -> extract -> embed. Each tool reads its own table.

[extract]
source = "~/.relic-scan"        # relic-scan's output: YYYY-MM.parquet + meta/sessions.parquet
out = "~/.relic-extract"        # <stream>/YYYY-MM.parquet, ready for relic-embed
months = "changed"              # "changed" | "all" | ["2026-10", "2026-09"]
sessions = "any"                # cat/probe from meta/sessions.parquet: "any" tier (main preferred) | "main" only

[extract.dedupe]
key = "content"                 # "content": the same message rewritten with other bytes is embedded once
                                # "h": one row per truth row

[extract.chunk]
max_chars = 6000                # longer texts are cut, with this overlap
overlap = 400

[extract.streams.text]
enabled = true
field = "text"
roles = ["user", "assistant"]   # [] = every role

[extract.streams.text.clean]     # before cutting; msgkey stays on the raw row, key is on the cleaned chunk
enabled = true
strip_tags = ["system-reminder"]                 # <tag>…</tag> removed anywhere
commands = "args"               # slash commands: "args" -> "/goal <args>" (none: dropped) | "drop" | "keep"
drop_tags = ["task-notification", "subagent_notification", "goal_context", "hook_prompt", "local-command-stdout",
             "local-command-stderr", "local-command-caveat", "bash-input", "bash-stdout", "bash-stderr",
             "environment_context", "user_instructions"]   # a message starting with <tag is dropped
drop_prefixes = ["Stop hook feedback:", "Base directory for this skill:", "[Request interrupted by user",
                 "Caveat: The messages below were generated", "# AGENTS.md instructions", "API Error:",
                 "No response requested."]
drop_invisible = true           # nothing but whitespace / zero-width characters
min_chars = 0                   # v3 used 24; 0 = keep short messages
redact = true                   # WireGuard keys, Telegram / Discord tokens, Discord webhooks -> [kind:abcd…N]

[extract.streams.thinking]
enabled = false                 # Nat 2026-10-22: "just text no thinking for the embed"
field = "text"
roles = ["thinking"]

[extract.streams.tools]
enabled = false                 # Nat 2026-10-22: "next time we skip tools"
field = "body"
kinds = ["call"]                # "call" = tool inputs; add "result" for outputs
max_chars = 2000                # a tool body is cut here, not chunked

# [embed]                       # relic-embed (next): model, gb300 / local runs, output
"##;

fn clean_defaults() -> Value {
    json!({
        "enabled": true,
        "strip_tags": ["system-reminder"],
        "commands": "args",
        "drop_tags": ["task-notification", "subagent_notification", "goal_context", "hook_prompt", "local-command-stdout",
                      "local-command-stderr", "local-command-caveat", "bash-input", "bash-stdout", "bash-stderr",
                      "environment_context", "user_instructions"],
        "drop_prefixes": ["Stop hook feedback:", "Base directory for this skill:", "[Request interrupted by user",
                          "Caveat: The messages below were generated", "# AGENTS.md instructions", "API Error:",
                          "No response requested."],
        "drop_invisible": true,
        "min_chars": 0,
        "redact": true,
    })
}

fn defaults() -> Value {
    json!({"extract": {
        "source": "~/.relic-scan",
        "out": "~/.relic-extract",
        "months": "changed",
        "dedupe": {"key": "content"},
        "chunk": {"max_chars": 6000, "overlap": 400},
        "sessions": "any",
        "streams": {
            "text": {"enabled": true, "field": "text", "roles": ["user", "assistant"], "clean": clean_defaults()},
            "thinking": {"enabled": false, "field": "text", "roles": ["thinking"]},
            "tools": {"enabled": false, "field": "body", "kinds": ["call"], "max_chars": 2000},
        },
    }})
}

pub fn expand(p: &str) -> String {
    match p.strip_prefix("~") {
        Some(rest) if rest.is_empty() || rest.starts_with('/') => format!("{}{rest}", std::env::var("HOME").unwrap_or_default()),
        _ => p.to_string(),
    }
}

fn merge(base: &Value, over: &Value) -> Value {
    match (base, over) {
        (Value::Object(b), Value::Object(o)) => {
            let mut out: Map<String, Value> = b.clone();
            for (k, v) in o {
                let nv = match (out.get(k), v) {
                    (Some(bv @ Value::Object(_)), Value::Object(_)) => merge(bv, v),
                    _ => v.clone(),
                };
                out.insert(k.clone(), nv);
            }
            Value::Object(out)
        }
        _ => over.clone(),
    }
}

fn toml_to_json(v: toml::Value) -> Value {
    match v {
        toml::Value::String(s) => Value::String(s),
        toml::Value::Integer(i) => json!(i),
        toml::Value::Float(f) => json!(f),
        toml::Value::Boolean(b) => Value::Bool(b),
        toml::Value::Datetime(d) => Value::String(d.to_string()),
        toml::Value::Array(a) => Value::Array(a.into_iter().map(toml_to_json).collect()),
        toml::Value::Table(t) => Value::Object(t.into_iter().map(|(k, v)| (k, toml_to_json(v))).collect()),
    }
}

/// The settings in effect: the [extract] table merged over the defaults, ~ expanded.
pub struct Config {
    pub v: Value,
    pub path: PathBuf,
    pub existed: bool,
}

impl Config {
    pub fn source(&self) -> &str { self.v["source"].as_str().unwrap_or("") }
    pub fn out(&self) -> &str { self.v["out"].as_str().unwrap_or("") }
    pub fn stream(&self, name: &str) -> &Value { &self.v["streams"][name] }

    /// The Python reference's behaviour: every role, no clean step, main-tier sessions (`run --raw`, `just parity`).
    pub fn raw(&mut self) {
        for s in STREAMS {
            if let Some(m) = self.v["streams"][s].as_object_mut() {
                m.remove("roles");
                m.remove("clean");
            }
        }
        self.v["sessions"] = Value::String("main".into());
    }
    pub fn content_dedupe(&self) -> bool { self.v["dedupe"]["key"] == "content" }
    pub fn max_chars(&self) -> usize { self.v["chunk"]["max_chars"].as_u64().unwrap_or(6000) as usize }
    pub fn overlap(&self) -> usize { self.v["chunk"]["overlap"].as_u64().unwrap_or(400) as usize }

    /// What a part of this stream depends on, besides its source month: change it and every month is cut again.
    /// Same bytes as the Python version (json.dumps sort_keys -> blake2b-8), so its parts stay fresh.
    pub fn stream_hash(&self, name: &str) -> String {
        let mut deps = json!({"stream": self.stream(name), "dedupe": self.v["dedupe"], "chunk": self.v["chunk"]});
        if self.v["sessions"] != "main" {
            deps["sessions"] = self.v["sessions"].clone(); // "main" hashes as before, so --raw matches the Python version
        }
        blake2b_simd::Params::new().hash_length(8).hash(crate::json::py_dumps(&deps).as_bytes()).to_hex().to_string()
    }
}

pub fn path_of(given: Option<&str>) -> PathBuf {
    let p = given.map(str::to_string).or_else(|| std::env::var("ARRA_CONFIG").ok()).unwrap_or("~/.arra/relic.toml".into());
    PathBuf::from(expand(&p))
}

pub fn load(given: Option<&str>) -> Result<Config, String> {
    let path = path_of(given);
    let existed = path.exists();
    let raw = if existed {
        let text = fs::read_to_string(&path).map_err(|e| format!("{}: {e}", path.display()))?;
        toml_to_json(toml::Value::Table(toml::from_str(&text).map_err(|e| format!("{}: {e}", path.display()))?))
    } else {
        json!({})
    };
    let mut v = merge(&defaults(), &raw)["extract"].clone();
    for k in ["source", "out"] {
        let s = expand(v[k].as_str().ok_or(format!("{}: [extract] {k} must be a string", path.display()))?);
        v[k] = Value::String(s);
    }
    let p = path.display();
    let bad: Vec<&String> = v["streams"].as_object().map(|m| m.keys().filter(|k| !STREAMS.contains(&k.as_str())).collect())
        .unwrap_or_default();
    if !bad.is_empty() {
        let bad: Vec<&str> = bad.iter().map(|s| s.as_str()).collect();
        return Err(format!("{p}: unknown stream(s) {} (known: {})", bad.join(", "), STREAMS.join(", ")));
    }
    if !matches!(v["dedupe"]["key"].as_str(), Some("content" | "h")) {
        return Err(format!("{p}: [extract.dedupe] key must be \"content\" or \"h\""));
    }
    let (mc, ov) = (v["chunk"]["max_chars"].as_i64().unwrap_or(-1), v["chunk"]["overlap"].as_i64().unwrap_or(-1));
    if !(0 <= ov && ov < mc) {
        return Err(format!("{p}: [extract.chunk] needs 0 <= overlap < max_chars"));
    }
    if !matches!(v["sessions"].as_str(), Some("any" | "main")) {
        return Err(format!("{p}: [extract] sessions must be \"any\" or \"main\""));
    }
    match &v["months"] {
        Value::String(s) if s == "changed" || s == "all" => {}
        Value::Array(a) if a.iter().all(Value::is_string) => {}
        _ => return Err(format!("{p}: [extract] months must be \"changed\", \"all\" or a list of \"YYYY-MM\"")),
    }
    Ok(Config { v, path, existed })
}

/// Write the template if no config is there. Returns (path, written).
pub fn init(given: Option<&str>) -> std::io::Result<(PathBuf, bool)> {
    let p = path_of(given);
    if p.exists() {
        return Ok((p, false));
    }
    if let Some(d) = p.parent() {
        fs::DirBuilder::new().recursive(true).mode(0o700).create(d)?;
    }
    fs::write(&p, TEMPLATE)?;
    Ok((p, true))
}

pub fn private_dir(d: &Path) -> std::io::Result<()> {
    fs::DirBuilder::new().recursive(true).mode(0o700).create(d)
}

pub fn private_file(f: &Path) -> std::io::Result<()> {
    fs::set_permissions(f, fs::Permissions::from_mode(0o600))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn raw_text_hash_matches_python() {
        // ~/.relic-extract/text/_extract.json written by the Python version with the default settings
        let mut c = Config { v: defaults()["extract"].clone(), path: PathBuf::new(), existed: false };
        let cleaned = c.stream_hash("text");
        c.raw();
        assert_eq!(c.stream_hash("text"), "f4fda3dd0075a191");
        assert_ne!(cleaned, "f4fda3dd0075a191"); // the clean step's settings re-cut every month
    }

    #[test]
    fn template_is_the_defaults() {
        let t = toml_to_json(toml::Value::Table(toml::from_str(TEMPLATE).unwrap()));
        assert_eq!(merge(&defaults(), &t), defaults());
    }
}
