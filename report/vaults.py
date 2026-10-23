"""ψ vault notes as one more stream: ~/.relic-extract/vault/notes.parquet, one row per chunk, the same shape as the others.

    uv run python report/vaults.py

relic-scan lists every vault and note (meta/vaults.json, meta/vaults/<id>.json). This reads each markdown note of the
own and plain vaults (git worktree copies are skipped: they duplicate their vault), 300 B to 2 MB, cuts it like the
text stream (6000 characters, 400 overlap), keys each chunk by blake2b-128 of its text (the embedding cache key, so a
note mirrored in several vaults is embedded once), and redacts the same secrets the clean step does. Columns match
the transcript streams where they can: msgkey = md5(vault path + note path), ts / ts_th = the note's mtime,
role = "note", cat = the vault's oracle, so embed_streams.py and search.py treat it like any stream.
"""

import hashlib
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

HOME = Path.home()
META = HOME / ".relic-scan" / "meta"
OUT = HOME / ".relic-extract" / "vault"
MAX, OVER = 6000, 400
TH = timezone(timedelta(hours=7))
REDACT = [
    ("wireguard-key", re.compile(r"(?i)\bPrivateKey\s*=\s*([A-Za-z0-9+/]{42,43}=)"), 1),
    ("telegram-token", re.compile(r"\b([0-9]{8,10}:AA[A-Za-z0-9_-]{33})\b"), 1),
    ("discord-webhook", re.compile(r"discord(?:app)?\.com/api/webhooks/[0-9]+/([A-Za-z0-9_-]{50,})"), 1),
    ("discord-token", re.compile(r"\b([MN][A-Za-z0-9_-]{23,25}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,38})\b"), 1),
    ("github-token", re.compile(r"\b((?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b"), 1),
    ("api-key", re.compile(r"\b(sk-(?:ant-|proj-)?[A-Za-z0-9_-]{24,})\b"), 1),
]


def redact(s):
    for kind, rx, g in REDACT:
        s = rx.sub(lambda m: m.group(0).replace(m.group(g), f"[{kind}:{m.group(g)[:4]}…{len(m.group(g))}]"), s)
    return s


def chunks(text):
    if len(text) <= MAX:
        return [text]
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i + MAX])
        if i + MAX >= len(text):
            break
        i += MAX - OVER
    return out


def main():
    t0 = time.time()
    vaults = json.loads((META / "vaults.json").read_text())["vaults"]
    cols = {k: [] for k in ("key", "msgkey", "chunk", "month", "sid", "ts", "ts_th", "engine", "role", "type", "kind", "name",
                            "cat", "probe", "text", "vault", "path", "section", "title")}
    n_notes = n_skip = 0
    for v in vaults:
        if v["kind"] == "worktree":
            continue
        f = META / "vaults" / f"{v['id']}.json"
        if not f.exists():
            continue
        root = Path(v["path"])
        for rel, sec, title, size, mt in json.loads(f.read_text())["items"]:
            if not rel.endswith(".md") or not 300 <= size <= 2_000_000:
                n_skip += 1
                continue
            try:
                text = (root / rel).read_text(errors="replace").strip()
            except OSError:
                n_skip += 1
                continue
            if not text:
                continue
            text = redact(text)
            ts = datetime.fromtimestamp(mt / 1000, timezone.utc)
            msgkey = hashlib.md5(f"{v['path']}\0{rel}".encode()).hexdigest()
            for i, c in enumerate(chunks(text)):
                for k, val in (("key", hashlib.blake2b(c.encode(), digest_size=16).hexdigest()), ("msgkey", msgkey), ("chunk", i),
                               ("month", ts.astimezone(TH).strftime("%Y-%m")), ("sid", f"vault:{v['id']}"),
                               ("ts", ts.strftime("%Y-%m-%dT%H:%M:%S.000Z")), ("ts_th", ts.astimezone(TH).isoformat(timespec="milliseconds")),
                               ("engine", "vault"), ("role", "note"), ("type", "note"), ("kind", ""), ("name", sec), ("cat", v["name"]),
                               ("probe", False), ("text", c), ("vault", v["kind"]), ("path", rel), ("section", sec), ("title", title)):
                    cols[k].append(val)
            n_notes += 1
    OUT.mkdir(parents=True, exist_ok=True)
    tab = pa.table(cols)
    pq.write_table(tab, OUT / "notes.parquet.part", compression="zstd")
    (OUT / "notes.parquet.part").replace(OUT / "notes.parquet")
    (OUT / "notes.parquet").chmod(0o600)
    print(f"vaults: {n_notes:,} notes -> {tab.num_rows:,} chunks · {len(set(cols['key'])):,} distinct texts · {n_skip:,} skipped · "
          f"{time.time() - t0:.0f}s -> {OUT / 'notes.parquet'}")


if __name__ == "__main__":
    main()
