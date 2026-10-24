"""The 15-minute deep gb300 lane from its cache: how many windows carry friction and lesson, and one window that
has both (the first, or the first on DAY).    python3 deep.py any|YYYY-MM-DD [N]"""
import json
import os
import sys

c = json.load(open(os.path.expanduser("~/.relic-extract/report/readings-cache-15m-gb300-qwen3_14b-deep.json")))
day = sys.argv[1]
real = lambda v, k: v.get(k) not in (None, "", "none")
deep = {k: v for k, v in c.items() if "friction" in v}
print(f"{len(c):,} windows in the cache · {len(deep):,} read with the deep keys · friction named in {sum(real(v, 'friction') for v in deep.values()):,}"
      f" · lesson named in {sum(real(v, 'lesson') for v in deep.values()):,}")
hits = [(k, v) for k, v in sorted(deep.items()) if (day == "any" or k.startswith(day)) and real(v, "friction") and real(v, "lesson")]
for k, v in hits[: int(sys.argv[2]) if len(sys.argv) > 2 else 1]:
    print(json.dumps({"window": k, **{x: v.get(x) for x in ("type", "focus", "friction", "lesson", "th")}}, ensure_ascii=False, indent=1))
