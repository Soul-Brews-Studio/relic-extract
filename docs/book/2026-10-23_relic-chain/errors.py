#!/usr/bin/env python3
"""The day's real errors, read back from this session's own transcript (tool results only).
    python3 errors.py <session.jsonl>
One line per failure: the first time its error text appeared (Bangkok) and the shortest line that names it."""
import json, re, sys
from datetime import datetime, timedelta

PATS = [("duckdb alias", r'Parser Error: syntax error at or near "(text|key|days|hours|last)"'),
        ("z.ai 429", r"HTTP Error 429"),
        ("z.ai 1302", r'"code":\s*"?1302'),
        ("z.ai 1210", r'"code":\s*"?1210'),
        ("hook exit", r"after: exited \d+")]
seen = {}
for line in open(sys.argv[1], encoding="utf-8"):
    try:
        e = json.loads(line)
    except Exception:
        continue
    if e.get("type") != "user":
        continue
    c = e.get("message", {}).get("content")
    if not isinstance(c, list):
        continue
    for b in c:
        if b.get("type") != "tool_result":
            continue
        t = b.get("content")
        t = "\n".join(x.get("text", "") for x in t if isinstance(x, dict)) if isinstance(t, list) else str(t or "")
        for name, p in PATS:
            if name in seen:
                continue
            for ln in t.splitlines():
                if re.search(p, ln):
                    ts = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")) + timedelta(hours=7)
                    seen[name] = (ts.strftime("%H:%M"), re.sub(r"\s+", " ", ln.strip())[:70])
                    break
for name, _ in PATS:
    if name in seen:
        print(f"{seen[name][0]}  {name:<13} {seen[name][1]}")
