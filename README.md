# relic-extract

Step 2 of the relic chain: **scan -> extract -> embed**.

```
 relic-scan              relic-extract                         relic-embed (next)         relic4
 find + parse       ──►  pick streams, dedupe, cut        ──►  vectors              ──►  search
 ~/.relic-scan/          ~/.relic-extract/<stream>/            gb300 / local             CLI · API · MCP · web
   YYYY-MM.parquet         YYYY-MM.parquet
   meta/sessions.parquet
```

It reads the month files [relic-scan](https://github.com/Soul-Brews-Studio/relic4-scan) writes. Then it writes, for each stream that is on, one Parquet part per month: one row per chunk to embed. What goes in is set in one TOML file, `~/.arra/relic.toml`.

## Use

One binary, `relic-extract` (Rust, `src/*.rs`). No Python or DuckDB needed on the machine.

```sh
just install                        # build, then put relic-extract in ~/.local/bin
relic-extract init                  # write ~/.arra/relic.toml with the defaults (kept if it exists)
relic-extract run                   # only months whose source changed, and streams whose settings changed
relic-extract run --months 2026-10 --stream text --force
relic-extract status                # per stream: months, chunks, distinct texts, newest message
relic-extract config                # the settings in effect (the file merged over the defaults)
relic-extract analyse               # what a run would cut and what the clean step takes out; writes nothing
relic-extract analyse --months 2026-10 --what-if min_chars=24 --what-if chunk.max_chars=2000
```

`analyse` runs the same select / clean / cut as `run`, in memory, and prints: totals (raw cut -> other roles ->
cleaned out -> kept, chunks, distinct texts), a table by month, each clean rule with its messages, characters and a
sample, what strip_tags / commands / redact did to the messages that stay, chunks per message and the biggest
messages, the most repeated texts (loops show up here), and chunks per repository. `--what-if KEY=VALUE`
(repeatable) adds a second column with the setting changed; a short key is looked up in `streams.<stream>.clean`,
then `streams.<stream>`, then `chunk`, then `[extract]`. Nothing is written.

`--config FILE` or `ARRA_CONFIG` points to another config.

The Python version (`src/relic_extract`, `uv run relic-extract …`) is kept as the reference: `just parity` cuts every
month with the binary into `~/.relic-extract-parity` and compares it with `~/.relic-extract` row by row, every column,
and the row order. Both write the same `_extract.json` hash, so either can continue after the other.

## ~/.arra/relic.toml

One file for the whole chain, with nested tables per tool. relic-extract reads `[extract]`. `[scan]` and `[embed]` are kept for relic-scan and relic-embed. A missing file or key falls back to the defaults. The defaults are jsonl-truth's `embed/workflow.toml` choices as of 2026-10-22, so a machine with no config gets what the fleet already runs.

```toml
[extract]
source = "~/.relic-scan"        # relic-scan's output
out = "~/.relic-extract"        # <stream>/YYYY-MM.parquet
months = "changed"              # "changed" | "all" | ["2026-10", "2026-09"]
sessions = "any"                # cat/probe from meta/sessions.parquet: "any" tier (main preferred) | "main" only

[extract.dedupe]
key = "content"                 # "content": a message rewritten with other bytes is embedded once · "h": every row

[extract.chunk]
max_chars = 6000
overlap = 400

[extract.streams.text]
enabled = true
field = "text"
roles = ["user", "assistant"]   # [] = every role

[extract.streams.text.clean]     # before cutting; msgkey stays on the raw row, key is on the cleaned chunk
enabled = true
strip_tags = ["system-reminder"]                 # <tag>…</tag> removed anywhere
commands = "args"               # slash commands: "args" -> "/goal <args>" (none: dropped) | "drop" | "keep"
drop_tags = ["task-notification", "subagent_notification", "goal_context", "hook_prompt", "local-command-stdout", …]
drop_prefixes = ["Stop hook feedback:", "Base directory for this skill:", "[Request interrupted by user", …]
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
kinds = ["call"]                # add "result" for tool outputs
max_chars = 2000                # a tool body is cut here, not chunked
```

## Output

`~/.relic-extract/<stream>/YYYY-MM.parquet`, one row per chunk:

| column | |
|---|---|
| `key` | blake2b-128 of the chunk text: the embedding cache key (same text, same vector, any month) |
| `msgkey`, `chunk` | the message (md5 of its content columns, as in agent-relic-v4) and the chunk number within it |
| `h`, `n_h` | one row holding the message (smallest `h`) and how many rows hold it |
| `month`, `sid`, `ts`, `ts_th`, `engine`, `role`, `type`, `kind`, `name` | from the month file |
| `cat`, `probe` | the session's repo and whether it is an automated probe, from relic-scan's `meta/sessions.parquet` |
| `text` | the chunk |

`<stream>/_extract.json` records the settings a stream was cut with. Change them and every month of that stream is cut again.

The cut and the keys are the same as agent-relic-v4's `split` (recipe `text-v1`) and jsonl-truth's `embed/export.py`. A chunk's `key` therefore finds a vector either of them already made.

## Docs

- `docs/SCAN-INPUT.md`: relic-scan's output, read from its source and checked against the data (10 rounds).
- `docs/LITERATURE.md`: what earlier relic generations (v1-v4, relic-lessons, relic4-scan) decided and measured about
  extraction, keys, chunking, storage, FTS/ICU and LanceDB.
