"""Seconds per answer, per lane, from readings.jsonl (every answer days.py, blocks.py and readings.py got back)."""
import json
import os
import statistics as st

def grain(u):
    """readings.py: "2025-09-19 15:00-15:15 15m" / "2025-10-24 day"; blocks.py: "2025-09-19 15" (3h), "2025-09-19 15-1h"."""
    last = u.split()[-1]
    if last in ("15m", "1h", "3h", "day"):
        return last
    if last.endswith("-1h"):
        return "1h"
    return "3h" if len(last) == 2 else "day"


L = {}
for line in open(os.path.expanduser("~/.relic-extract/report/readings.jsonl")):
    try:
        r = json.loads(line)
    except ValueError:
        continue
    L.setdefault((r["model"], grain(r["unit"])), []).append(r.get("secs") or 0)
for (m, g), v in sorted(L.items(), key=lambda x: (x[0][0].split(":")[0] == "zai", x[0][0], x[0][1])):
    print(f"{m:<24} {g:>4} {len(v):>7,} answers  median {st.median(v):5.1f} s")
