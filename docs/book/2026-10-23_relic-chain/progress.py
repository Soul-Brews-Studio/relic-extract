"""How far each running lane is: windows in its cache against the windows it will read, and the pace of the
last 30 minutes from readings.jsonl."""
import json
import os
from datetime import datetime

R = os.path.expanduser("~/.relic-extract/report/")
now = datetime.now().astimezone()
print(f"at {now:%Y-%m-%d %H:%M} (+07)")
# the gb300 total is the count readings.py printed at its start (capture 108); the z.ai lanes are re-read in turn
for tag, total in (("15m-gb300-qwen3_14b-deep", 15143),):
    c = json.load(open(R + f"readings-cache-{tag}.json"))
    deep = sum("friction" in v for v in c.values())
    print(f"  {tag:<26} {deep:>6,} / {total:>6,}  {deep / total:6.1%}  read with friction + lesson")
for tag in ("day-zai-glm-5.3", "3h-zai-glm-5.3", "1h-zai-glm-5.3"):
    print(f"  {tag:<26} {len(json.load(open(R + f'readings-cache-{tag}.json'))):>6,} windows cached")
pace = {}
for line in open(R + "readings.jsonl"):
    try:
        r = json.loads(line)
    except ValueError:
        continue
    at = datetime.strptime(r["at"], "%Y-%m-%dT%H:%M:%S%z")
    if (now - at).total_seconds() <= 1800:
        pace.setdefault(r["model"], []).append(at)
for m, ts in sorted(pace.items()):
    print(f"  last 30 min  {m:<22} {len(ts):>5} answers  {(ts[-1] - ts[0]).total_seconds() / max(len(ts) - 1, 1):5.2f} s apart")
