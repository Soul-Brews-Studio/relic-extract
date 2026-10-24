"""The lane comparison the page draws (windows.js winCompare), printed: one row per lane plus the day readings,
then how often two models give the same type to the same window. Reads ~/.relic-extract/report/report.json."""
import json
import os
import sys
from collections import Counter, defaultdict

D = json.load(open(os.path.expanduser("~/.relic-extract/report/report.json")))
W = dict(D.get("windows", {}))
days = D["days"]["days"]
W["day gb300"] = dict(unit="day", host="gb300", rows=[[d["day"], 0, d["summary"]["type"], (d.get("shape") or {}).get("top_project"), d.get("prompts_main", 0)]
                                                      for d in days if d.get("summary") and d["summary"].get("type")])
top = {d["day"]: (d.get("shape") or {}).get("top_project") for d in days}
order = lambda k: ["day", "3h", "1h", "15m"].index(W[k]["unit"]) * 10 + (0 if W[k]["host"] == "gb300" else 1) + (2 if W[k].get("deep") else 0)
keys = sorted([k for k in W if W[k]["rows"]], key=order)
mode = sys.argv[1] if len(sys.argv) > 1 else "table"
if mode == "table":
    print(f"{'lane':<14}{'windows':>8}{'days':>6}{'build':>7}{'ops':>6}{'fix':>6}{'res+wr':>8}{'mix+pl':>8}{'lead':>7}{'proj/d':>8}")
    for k in keys:
        R = W[k]["rows"]; n = len(R); by = defaultdict(list)
        for r in R: by[r[0]].append(r)
        sh = lambda *t: f"{sum(r[2] in t for r in R) / n:.0%}"
        lead = fp = "-"
        if W[k]["unit"] != "day":  # windows.js leadStats: days with 3+ windows, each day's share averaged
            ds = [[r for r in rs if r[3]] for d, rs in by.items() if len(rs) >= 3 and top.get(d)]
            ds = [rs for rs in ds if rs]
            if ds:
                lead = f"{sum(sum(r[3] == top[r[0]] for r in rs) / len(rs) for rs in ds) / len(ds):.0%}"
                fp = f"{sum(len({r[3] for r in rs}) for rs in ds) / len(ds):.2f}"
        print(f"{k:<14}{n:>8,}{len(by):>6}{sh('build'):>7}{sh('ops'):>6}{sh('fix'):>6}{sh('research', 'writing'):>8}{sh('mixed', 'planning'):>8}{lead:>7}{fp:>8}")
else:
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if W[a]["unit"] != W[b]["unit"] or W[a]["host"] == W[b]["host"]:
                continue
            ta = {(r[0], r[1]): r[2] for r in W[a]["rows"]}
            both = [(ta[(r[0], r[1])], r[2]) for r in W[b]["rows"] if (r[0], r[1]) in ta]
            if len(both) < 30:
                continue
            same = sum(x == y for x, y in both)
            print(f"{W[a]['unit']}: {a} vs {b}  {len(both):,} windows both read  same type {same / len(both):.0%}")
            for (x, y), n in Counter((x, y) for x, y in both if x != y).most_common(5):
                print(f"    {a.split()[1]} {x:<9} / {b.split()[1]} {y:<9} {n:>5,}")
