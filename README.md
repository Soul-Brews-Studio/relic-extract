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
```

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

[extract.dedupe]
key = "content"                 # "content": a message rewritten with other bytes is embedded once · "h": every row

[extract.chunk]
max_chars = 6000
overlap = 400

[extract.streams.text]
enabled = true
field = "text"

[extract.streams.thinking]
enabled = false                 # Nat 2026-10-22: "just text no thinking for the embed"
field = "text"

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
