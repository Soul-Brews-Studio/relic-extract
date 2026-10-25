"""gb300 (qwen3:14b) against z.ai (glm-5.3) on the same windows, from the two lanes' own caches.

    python3 vs.py agree      # per grain: windows both read, same type, the splits, each model's type mix
    python3 vs.py speed      # seconds per answer, per grain and model
    python3 vs.py friction   # 15m deep: how often each says "none", and when they disagree about it
    python3 vs.py opening    # how each model's English reading starts ("The day was ..." in a 15-minute window)
    python3 vs.py months     # 15m: agreement and friction found, month by month
    python3 vs.py pace DATE  # gb300 15m answers per hour on DATE, from readings.jsonl
    python3 vs.py trial      # the five-model trial on 198 shared 3-hour windows (status.json)

Counts and model names only, except `opening`, which prints the first four words of each reading.
"""
import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

R = os.path.expanduser("~/.relic-extract/report")
TYPES = ("build", "fix", "ops", "research", "writing", "planning", "mixed")


def load(f):
    return json.load(open(f"{R}/{f}"))


def norm(k):
    """'qwen3:14b|2026-06-06|18' / 'qwen3:14b|2026-06-06|18-1h' / '2026-06-06 18:00-21:00' / '2026-06-06' -> one key."""
    if "|" in k:
        p = k.split("|")
        if len(p) == 2:
            return p[1]
        return f"{p[1]} {p[2].split('-')[0]}:00"
    m = re.match(r"(\d{4}-\d\d-\d\d)(?: (\d\d:\d\d))?", k)
    return m.group(1) + (f" {m.group(2)}" if m.group(2) else "")


def pair(gb, zai, prefix=None):
    G = {norm(k): v for k, v in load(gb).items() if prefix is None or k.startswith(prefix)}
    Z = {norm(k): v for k, v in load(zai).items()}
    return G, Z


GRAINS = [("day", "days-cache.json", "readings-cache-day-zai-glm-5.3.json", "qwen3:14b|"),
          ("3h", "blocks-cache.json", "readings-cache-3h-zai-glm-5.3.json", None),
          ("1h", "blocks-cache-1h.json", "readings-cache-1h-zai-glm-5.3.json", None),
          ("15m", "readings-cache-15m-gb300-qwen3_14b-deep.json", "readings-cache-15m-zai-glm-5.3-deep.json", None)]


def mix(vs):
    c = Counter(v.get("type") for v in vs)
    return " ".join(f"{t} {c[t] / len(vs):.0%}" for t in TYPES if c[t] / len(vs) >= 0.01)


def agree():
    for g, gf, zf, pre in GRAINS:
        G, Z = pair(gf, zf, pre)
        both = sorted(set(G) & set(Z))
        same = sum(G[k].get("type") == Z[k].get("type") for k in both)
        splits = Counter((G[k].get("type"), Z[k].get("type")) for k in both if G[k].get("type") != Z[k].get("type"))
        print(f"{g:>4}: gb300 {len(G):>6,} · z.ai {len(Z):>6,} · both {len(both):>6,} · same type {same / len(both):.0%} ({same:,})")
        print(f"      splits gb300/z.ai: " + ", ".join(f"{a}/{b} {n:,}" for (a, b), n in splits.most_common(4)))
        print(f"      gb300 says: {mix([G[k] for k in both])}")
        print(f"      z.ai  says: {mix([Z[k] for k in both])}")


def speed():
    print(f"{'grain':>5} {'model':<16}{'answers':>9}{'median s':>10}{'p90 s':>8}")
    for g, gf, zf, pre in GRAINS:
        G, Z = pair(gf, zf, pre)
        for name, C in (("gb300 qwen3:14b", G), ("z.ai glm-5.3", Z)):
            s = sorted(v["secs"] for v in C.values() if isinstance(v.get("secs"), (int, float)))
            print(f"{g:>5} {name:<16}{len(s):>9,}{statistics.median(s):>10.1f}{s[int(len(s) * .9)]:>8.1f}")


def none(v, k):
    t = str(v.get(k) or "").strip().lower().rstrip(".")
    return t in ("", "none", "n/a") or t.startswith("none ") or t.startswith("nothing")


def friction():
    G, Z = pair(*GRAINS[3][1:3])
    both = sorted(set(G) & set(Z))
    print(f"15m windows read deep by both: {len(both):,}")
    for k in ("friction", "lesson"):
        gn = sum(none(G[w], k) for w in both); zn = sum(none(Z[w], k) for w in both)
        c = Counter((none(G[w], k), none(Z[w], k)) for w in both)
        print(f"  {k}: 'none' from gb300 {gn / len(both):.0%} · from z.ai {zn / len(both):.0%}")
        print(f"     both found one {c[(False, False)]:,} · only z.ai {c[(True, False)]:,} · only gb300 {c[(False, True)]:,} · neither {c[(True, True)]:,}")
        gl = [len(str(G[w][k])) for w in both if not none(G[w], k)]; zl = [len(str(Z[w][k])) for w in both if not none(Z[w], k)]
        print(f"     median length when found: gb300 {statistics.median(gl) if gl else 0:.0f} chars · z.ai {statistics.median(zl) if zl else 0:.0f} chars")
    nf = Counter(G[w].get("type") for w in both if not none(Z[w], "friction"))
    print("  windows where z.ai found friction, by gb300's type: " + ", ".join(f"{t} {n:,}" for t, n in nf.most_common(5)))


def opening():
    for g, gf, zf, pre in GRAINS:
        G, Z = pair(gf, zf, pre)
        for name, C in (("gb300", G), ("z.ai", Z)):
            c = Counter(" ".join(str(v.get("en") or "").split()[:4]) for v in C.values())
            top = c.most_common(3)
            print(f"{g:>4} {name:<6} {len(C):>6,} readings · top openings: " + " | ".join(f'"{t}" {n / len(C):.0%}' for t, n in top))


def months():
    G, Z = pair(*GRAINS[3][1:3])
    by = defaultdict(list)
    for w in set(G) & set(Z):
        by[w[:7]].append(w)
    print(f"{'month':<8}{'both':>7}{'same':>7}{'z.ai friction':>15}{'gb300 friction':>16}")
    for m in sorted(by):
        ws = by[m]
        print(f"{m:<8}{len(ws):>7,}{sum(G[w].get('type') == Z[w].get('type') for w in ws) / len(ws):>7.0%}"
              f"{sum(not none(Z[w], 'friction') for w in ws) / len(ws):>15.0%}{sum(not none(G[w], 'friction') for w in ws) / len(ws):>16.0%}")


def pace(day):
    c = Counter(); secs = defaultdict(list)
    with open(f"{R}/readings.jsonl", "rb") as fh:
        fh.seek(max(0, os.path.getsize(f"{R}/readings.jsonl") - 400_000_000)); fh.readline()
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("model") == "gb300:qwen3:14b deep" and r.get("at", "").startswith(day):
                h = r["at"][11:13]; c[h] += 1; secs[h].append(r.get("secs") or 0)
    print(f"gb300 qwen3:14b, 15m deep, {day} (Bangkok)\n hour  answers  median s")
    for h in sorted(c):
        print(f"  {h}:00 {c[h]:>8} {statistics.median(secs[h]):>9.1f}")


def example(w=None):
    """One 15-minute window both read deep, side by side: type, focus, friction, lesson (each cut to 150 chars)."""
    G, Z = pair(*GRAINS[3][1:3])
    if w is None:  # the first window of 2026-06-10 where they give different types and only z.ai names a friction
        w = next(k for k in sorted(set(G) & set(Z)) if k.startswith("2026-06-10") and G[k].get("type") != Z[k].get("type")
                 and none(G[k], "friction") and not none(Z[k], "friction"))
    print(f"window {w}")
    for name, C in (("gb300 qwen3:14b", G), ("z.ai glm-5.3", Z)):
        v = C[w]
        print(f"-- {name} · {v.get('secs')} s")
        for k in ("type", "focus", "friction", "lesson"):
            print(f"  {k:<9}{str(v.get(k))[:150]}")


def trial():
    T = json.load(open(f"{R}/status.json"))["trial"]
    print(f"the same {T['windows']} 3-hour windows, five models (kept for gb300: {T['kept']})")
    print(f"  {'model':<26}{'median s':>9}{'same type as z.ai':>19}")
    for r in T["rows"]:
        print(f"  {r['model']:<26}{r['secs'] if r['secs'] is not None else '-':>9}{'reference' if r['agree'] is None else format(r['agree'], '.0%'):>19}")


m = sys.argv[1] if len(sys.argv) > 1 else "agree"
{"agree": agree, "speed": speed, "friction": friction, "opening": opening, "months": months, "trial": trial,
 "pace": lambda: pace(sys.argv[2]), "example": lambda: example(sys.argv[2] if len(sys.argv) > 2 else None)}[m]()
