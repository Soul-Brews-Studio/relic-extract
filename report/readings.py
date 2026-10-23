"""Read every window of time with a model: days, 3-hour or 1-hour blocks, or 15-minute windows; on gb300 or z.ai.

    uv run python report/readings.py --unit 15m --model zai:glm-5.3 --deep --workers 8
    uv run python report/readings.py --unit 1h  --model gb300:qwen3:14b

--model  gb300:<ollama model> (ssh tunnel to gb300's ollama, one request at a time) or zai:<model> (z.ai's
         Anthropic-compatible API, key from `pass show glm/zai-2`, never printed; --workers requests at a time)
--unit   day | 3h | 1h | 15m; a window is read when it holds at least --min main-session prompts
--deep   two more keys: friction (what went wrong or pushed back) and lesson (one lesson learned, or "none")
Same input as days.py (loops out, projects, switches, agent prompts) and the same v3 prompt. Cache per lane:
readings-cache-<lane>.json; every answer also goes to readings.jsonl. -> readings-<unit>-<lane>.json
"""

import argparse
import hashlib
import json
import re
import subprocess
import threading
import time
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import common
import days as dy

HOME = Path.home()
OUT = HOME / ".relic-extract" / "report"
UNITS = {"day": 1440, "3h": 180, "1h": 60, "15m": 15}
DEEP = '''
Also answer two more keys:
  "friction": "what went wrong, failed, was corrected or pushed back in this window (one sentence), or \\"none\\"",
  "lesson": "one lesson the person learned or should keep from this window (one sentence), or \\"none\\""'''
KEYS_DEEP = dy.KEYS + ("friction", "lesson")


def window_input(con, d, m0, m1):
    """day_input for minutes m0..m1 of day d (Bangkok)."""
    mins = "(cast(substr(x.ts_th, 12, 2) as int) * 60 + cast(substr(x.ts_th, 15, 2) as int))"
    cond = f"substr(x.ts_th, 1, 10) = ? and {mins} >= {m0} and {mins} < {m1}"
    rows = con.execute(f"""select substr(x.ts_th, 12, 5) AS hm, coalesce(ses.cat, x.cat) AS cat, x.text, x.key
                           from x left join ses using (sid) where x.role = 'user' and x.chunk = 0 and x.tier = 'main'
                           and {cond} order by x.ts_th""", [d]).fetchall()
    rows = [r for r in rows if len(r[2].strip()) >= 8]
    reps = Counter(r[3] for r in rows)
    seen, uniq = set(), []
    for r in rows:
        if reps[r[3]] < 3 and r[3] not in seen:
            seen.add(r[3])
            uniq.append(r)
    cats = Counter(r[1] for r in rows)
    agents = con.execute(f"""select coalesce(ses.cat, x.cat), any_value(x.text) from x left join ses using (sid)
                             where x.role = 'user' and x.chunk = 0 and x.tier <> 'main' and {cond} group by 1, x.key
                             order by 1, x.key limit 12""", [d]).fetchall()
    shape = dict(prompts=len(rows), distinct=len(uniq), loop_prompts=sum(n for n in reps.values() if n >= 3),
                 projects=len(cats), top_project=cats.most_common(1)[0][0] if cats else None,
                 top_share=round(cats.most_common(1)[0][1] / len(rows), 2) if rows else 0,
                 project_switches=sum(1 for a, b in zip(rows, rows[1:]) if a[1] != b[1]), agent_prompts=len(agents),
                 projects_top=cats.most_common(6))
    step = max(1, len(uniq) // 40)
    lines = "\n".join(f"{hm} [{cat}] {re.sub(r'\s+', ' ', tx)[:280]}" for hm, cat, tx, _ in uniq[::step][:40])
    alines = "\n".join(f"[{cat}] {re.sub(r'\s+', ' ', tx)[:200]}" for cat, tx in agents) or "(none)"
    return shape, lines, alines


_zkey = None


def _zai_call(model, prompt, think):
    global _zkey
    if _zkey is None:
        _zkey = subprocess.run(["pass", "show", "glm/zai-2"], capture_output=True, text=True).stdout.splitlines()[0].strip()
    b = {"model": model, "max_tokens": 16000, "messages": [{"role": "user", "content": prompt}]}
    if not think:
        b["thinking"] = {"type": "disabled"}
    req = urllib.request.Request("https://api.z.ai/api/anthropic/v1/messages", json.dumps(b).encode(),
                                 {"content-type": "application/json", "x-api-key": _zkey, "authorization": "Bearer " + _zkey,
                                  "anthropic-version": "2023-06-01"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                j = json.loads(r.read())
            break
        except Exception:
            if attempt == 4:
                raise
            time.sleep(5 * (attempt + 1))
    return "".join(c.get("text", "") for c in j.get("content", []) if c.get("type") == "text"), j.get("stop_reason")


def _parse(text, keys):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        a = json.loads(m.group(0))
    except Exception:
        return None
    return {k: a.get(k) for k in keys} if a.get("focus") else None


def ask_zai(model, prompt, keys):
    """GLM with thinking (better reading); if no JSON comes back (the thinking ran out the budget), once without."""
    text, stop = _zai_call(model, prompt, True)
    got = _parse(text, keys)
    if got is None:
        text, stop = _zai_call(model, prompt, False)
        got = _parse(text, keys)
        if got is None:
            return {"en": (text or "").strip()[:600], "th": "", "json_ok": False, "stop": stop}
        return got | {"json_ok": True, "think": False}
    return got | {"json_ok": True, "think": True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", default="15m", choices=list(UNITS))
    ap.add_argument("--model", default="zai:glm-5.3")
    ap.add_argument("--deep", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--min", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    t0 = time.time()
    lane, model = a.model.split(":", 1)
    span = UNITS[a.unit]
    keys = KEYS_DEEP if a.deep else dy.KEYS
    tag = f"{a.unit}-{lane}-{model.replace(':', '_')}{'-deep' if a.deep else ''}"
    con = common.connect(HOME / ".relic-scan", HOME / ".relic-extract")
    units = con.execute(f"""select substr(ts_th, 1, 10) d, ((cast(substr(ts_th, 12, 2) as int) * 60 + cast(substr(ts_th, 15, 2) as int)) // {span}) * {span} AS m0,
                            count(distinct msgkey) n from x where role = 'user' and chunk = 0 and tier = 'main' and ts_th <> ''
                            group by 1, 2 having count(distinct msgkey) >= ? order by 1, 2""", [a.min]).fetchall()
    if a.limit:
        units = units[: a.limit]
    print(f"readings: {len(units):,} windows of {a.unit} (>= {a.min} prompts) · {a.model} · deep={a.deep} · {time.time() - t0:.0f}s", flush=True)
    cache_f = OUT / f"readings-cache-{tag}.json"
    cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    jobs = []
    for d, m0, n in units:
        m0 = int(m0)
        shape, lines, alines = window_input(con, d, m0, m0 + span)
        if not shape["prompts"]:
            continue
        label = f"{d} {m0 // 60:02d}:{m0 % 60:02d}-{(m0 + span) // 60:02d}:{(m0 + span) % 60:02d}" if a.unit != "day" else d
        span_t = {"day": "one day", "3h": "one 3-hour block", "1h": "one hour", "15m": "15 minutes"}[a.unit]
        prompt = dy.PROMPT.format(span=span_t, day=label, nums=json.dumps(shape), lines=lines, agents=alines)
        if a.deep:
            prompt = prompt.replace("\nNumbers: ", DEEP + "\n\nNumbers: ", 1)
        jobs.append((label, shape, prompt))
    lock = threading.Lock()
    done = 0

    def one(job):
        label, shape, prompt = job
        h = hashlib.md5((a.model + prompt).encode()).hexdigest()
        if cache.get(label, {}).get("h") == h:
            return label, shape, cache[label], False
        t1 = time.time()
        ans = ask_zai(model, prompt, keys) if lane == "zai" else dy.ask(model, prompt)
        ans["secs"] = round(time.time() - t1, 1)
        dy.keep(f"{label} {a.unit}", a.model + (" deep" if a.deep else ""), prompt, ans, ans["secs"])
        return label, shape, dict(h=h, **ans), True

    tun = dy.tunnel("gb300", model) if lane == "gb300" else None
    out = []
    try:
        with ThreadPoolExecutor(max_workers=a.workers if lane == "zai" else 1) as ex:
            futs = [ex.submit(one, j) for j in jobs]
            for f in as_completed(futs):
                try:
                    label, shape, ans, new = f.result()
                except Exception as e:
                    print(f"  failed: {e.__class__.__name__}: {str(e)[:120]}", flush=True)
                    continue
                with lock:
                    cache[label] = ans
                    out.append(dict(window=label, shape=shape, reading={k: ans.get(k) for k in keys}))
                    done += 1
                    if new:
                        print(f"  {label} · {shape['prompts']} prompts · {shape['projects']} projects · {ans.get('secs')}s · "
                              f"{ans.get('type')} · {str(ans.get('focus'))[:70]}", flush=True)
                    if done % 25 == 0:
                        cache_f.write_text(json.dumps(cache, ensure_ascii=False))
    finally:
        cache_f.write_text(json.dumps(cache, ensure_ascii=False))
        cache_f.chmod(0o600)
        if tun:
            tun.terminate()
    out.sort(key=lambda r: r["window"])
    dst = OUT / f"readings-{tag}.json"
    dst.write_text(json.dumps(dict(built=time.strftime("%Y-%m-%d %H:%M"), unit=a.unit, model=a.model, deep=a.deep,
                                   windows=out), ensure_ascii=False))
    dst.chmod(0o600)
    print(f"readings: {len(out):,} windows · {time.time() - t0:.0f}s -> {dst}")


if __name__ == "__main__":
    main()
