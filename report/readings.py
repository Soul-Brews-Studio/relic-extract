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
import signal
import subprocess
import threading
import time
import urllib.error
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
                           and {cond} order by x.ts_th, x.key, cat, x.text""", [d]).fetchall()   # a full order: ties (same second, the merged homes) came back in any order, so the prompt and its cache hash changed run to run
    rows = [r for r in rows if len(r[2].strip()) >= 8]
    reps = Counter(r[3] for r in rows)
    seen, uniq = set(), []
    for r in rows:
        if reps[r[3]] < 3 and r[3] not in seen:
            seen.add(r[3])
            uniq.append(r)
    cats = Counter(r[1] for r in rows)
    agents = con.execute(f"""select coalesce(ses.cat, x.cat), min(x.text) from x left join ses using (sid)
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


_zkeys, _zlock, _zi = [], threading.Lock(), [0]
_zname = {}   # key -> its pass entry name, so a log line can say which key without printing it
ZAI_PASS = ("glm/zai-2", "glm/zai-3", "glm/nat-wrw")   # several keys share the load; a 429 on one backs off without stopping the rest


def _zai_key():
    with _zlock:
        if not _zkeys:
            for e in ZAI_PASS:
                k = subprocess.run(["pass", "show", e], capture_output=True, text=True).stdout.splitlines()
                if k and k[0].strip():
                    _zkeys.append(k[0].strip())
                    _zname[k[0].strip()] = e
        if not _zkeys:
            raise RuntimeError("z.ai: no key left (every key is out of balance)")
        _zi[0] += 1
        return _zkeys[_zi[0] % len(_zkeys)]


def _zai_drop(key):
    """z.ai 1113 (insufficient balance / no resource package) never heals within a run: stop using that key."""
    with _zlock:
        if key in _zkeys and len(_zkeys) > 1:
            _zkeys.remove(key)
            print(f"  z.ai: {_zname.get(key, '?')} is out of balance (1113), {len(_zkeys)} left", flush=True)


def _zai_call(model, prompt, think):
    # glm-5.3 always thinks (z.ai 1210 "cannot be disabled"): the second try just gives the thinking more room
    b = {"model": model, "max_tokens": 16000 if think else 32000, "messages": [{"role": "user", "content": prompt}]}
    data = json.dumps(b).encode()
    for attempt in range(9):
        key = _zai_key()
        req = urllib.request.Request("https://api.z.ai/api/anthropic/v1/messages", data,
                                     {"content-type": "application/json", "x-api-key": key, "authorization": "Bearer " + key,
                                      "anthropic-version": "2023-06-01"})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                j = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            body = e.read()
            if b"1113" in body or e.code == 401:
                _zai_drop(key)
            if attempt == 8:
                raise
            wait = e.headers.get("retry-after") if e.code == 429 else None
            secs = float(wait) if wait and wait.replace(".", "").isdigit() else min(120, 10 * 2 ** attempt if e.code == 429 else 5 * (attempt + 1))
            code = re.search(rb'"code":\s*"?(\d+)', body)
            # every retry is printed (key by its pass name, never the key): a rate limit used to be invisible in the pane
            print(f"  z.ai: HTTP {e.code} code {code.group(1).decode() if code else '-'} on {_zname.get(key, '?')}, "
                  f"try {attempt + 1}/9, retry in {secs:.0f}s", flush=True)
            time.sleep(secs)
        except Exception as e:
            if attempt == 8:
                raise
            print(f"  z.ai: {e.__class__.__name__} on {_zname.get(key, '?')}, try {attempt + 1}/9, retry in {5 * (attempt + 1)}s", flush=True)
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


def _stop(*_):
    # the first signal stops the run; ignore the rest (the pane closing sends SIGHUP right after a TERM), or a second
    # one lands inside the cache save in `finally` and the save is lost
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    raise KeyboardInterrupt


def main():
    # a kill (SIGTERM) runs the finally below like Ctrl-C does, so the cache is saved and the next run resumes
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGHUP, _stop)  # the pane closing (herdr pane close) sends SIGHUP
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", default="15m", choices=list(UNITS))
    ap.add_argument("--model", default="zai:glm-5.3")
    ap.add_argument("--deep", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--gb-workers", type=int, default=1, help="requests at a time on gb300 (default 1)")
    ap.add_argument("--min", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sample", type=int, default=0, help="read N windows spread evenly over the year (a model trial)")
    ap.add_argument("--windows", metavar="CACHE", help="read only the windows in this readings-cache file (the same trial set for every model)")
    ap.add_argument("--restamp", metavar="SINCE", help="give cached readings logged since SINCE (2026-10-24T14:40) the current prompt hash, then stop")
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
    if a.sample:  # every k-th window over the whole span, the same ones each run (a model trial against the lanes)
        units = units[:: max(1, len(units) // a.sample)][: a.sample]
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
        if a.unit == "15m":  # the day prompt's "the day" made 15-minute readings start "The day was focused on ..."
            for w0, w1 in (("Describe the day", "Describe these 15 minutes"), ("the day's prompts", "these 15 minutes' prompts"),
                           ("if the day stayed", "if these 15 minutes stayed"), ("the day was mostly about", "these 15 minutes were mostly about"),
                           ("worked today", "worked in these 15 minutes")):
                prompt = prompt.replace(w0, w1)
        if a.deep:
            prompt = prompt.replace("\nNumbers: ", DEEP + "\n\nNumbers: ", 1)
        jobs.append((label, shape, prompt))
    if a.restamp:
        # one-off after the tie-order fix: every prompt's hash moved, though a window read on today's data has not
        # changed. A cached reading logged at or after --restamp (and not from today, which still grows) takes the
        # new hash; the rest stay as they are and are read again.
        last, mt = {}, a.model + (" deep" if a.deep else "")
        for line in open(dy.LOG):
            r = json.loads(line)
            if r.get("model") == mt:
                last[r["unit"]] = max(last.get(r["unit"], ""), r["at"])
        today, kept, stale, ok = time.strftime("%Y-%m-%d"), 0, 0, 0
        for label, _, prompt in jobs:
            h, got = hashlib.md5((a.model + prompt).encode()).hexdigest(), cache.get(label)
            if not got or got.get("h") == h:
                ok += bool(got)
            elif last.get(f"{label} {a.unit}", "") >= a.restamp and not label.startswith(today) and (not a.deep or "friction" in got):
                got["h"], kept = h, kept + 1
            else:
                stale += 1
        cache_f.write_text(json.dumps(cache, ensure_ascii=False))
        cache_f.chmod(0o600)
        print(f"readings: restamp {tag}: {ok:,} already current · {kept:,} restamped (read since {a.restamp}) · {stale:,} left to read again")
        return
    if a.windows:  # --sample drifts as live windows arrive; a later trial reads the first trial's windows instead
        want = set(json.loads(Path(a.windows).expanduser().read_text()))
        jobs = [j for j in jobs if j[0] in want]
        print(f"readings: {len(jobs):,} windows from {Path(a.windows).name}", flush=True)
    lock = threading.Lock()
    done = 0

    def one(job):
        label, shape, prompt = job
        h = hashlib.md5((a.model + prompt).encode()).hexdigest()
        got = cache.get(label, {})
        # a deep reading cached without friction/lesson (days.ask dropped them before 2026-10-24 14:40) is read again
        if got.get("h") == h and (not a.deep or "friction" in got):
            return label, shape, got, False
        t1 = time.time()
        ans = ask_zai(model, prompt, keys) if lane == "zai" else dy.ask(model, prompt, keys=keys)
        ans["secs"] = round(time.time() - t1, 1)
        dy.keep(f"{label} {a.unit}", a.model + (" deep" if a.deep else ""), prompt, ans, ans["secs"])
        return label, shape, dict(h=h, **ans), True

    tun = dy.tunnel("gb300", model) if lane == "gb300" else None
    out = []
    # no `with`: leaving a with-block waits for every queued window (hours), so a kill never reached the save
    # gb300: one request at a time unless --gb-workers asks for more (ollama runs them side by side on the shared GPU)
    ex = ThreadPoolExecutor(max_workers=a.workers if lane == "zai" else a.gb_workers)
    try:
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
                          f"{ans.get('type')} · {str(ans.get('focus'))[:70]}"
                          + (f" · friction: {str(ans.get('friction'))[:50]}" if a.deep else ""), flush=True)
                if done % 25 == 0:
                    cache_f.write_text(json.dumps(cache, ensure_ascii=False))
    finally:
        ex.shutdown(wait=False, cancel_futures=True)
        cache_f.write_text(json.dumps(cache, ensure_ascii=False))
        cache_f.chmod(0o600)
        dy._TUN.clear()  # a request still in flight must not reopen the tunnel after we stop
        if tun:
            tun.terminate()
    out.sort(key=lambda r: r["window"])
    dst = OUT / f"{'trial' if a.sample or a.windows else 'readings'}-{tag}.json"   # a --sample trial is not a lane: build.py reads readings-*.json
    dst.write_text(json.dumps(dict(built=time.strftime("%Y-%m-%d %H:%M"), unit=a.unit, model=a.model, deep=a.deep,
                                   windows=out), ensure_ascii=False))
    dst.chmod(0o600)
    print(f"readings: {len(out):,} windows · {time.time() - t0:.0f}s -> {dst}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:  # a stop (TERM, HUP, Ctrl-C): the cache was saved in main's finally; no traceback
        print("readings: stopped, cache saved; the next run resumes from it", flush=True)
        raise SystemExit(130)
