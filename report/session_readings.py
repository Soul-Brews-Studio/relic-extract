"""Read every main session once with a model: what it was about, what it did, how it ended, what it left open (relic5 #280).

    uv run python report/session_readings.py --model zai:glm-5.3 --workers 8 --since 2026-10-01
    uv run python report/session_readings.py --model fm:system --fm-hosts local --limit 50
    uv run python report/session_readings.py --plan

Window readings (readings.py) read a stretch of time across every session in it; nothing said what ONE session was
about, so relic5 showed a session that built a whole library as "hello". This reads each session's own prompts, its
first and last replies and the files it edited, and asks the same lanes as readings.py (zai, gb300, fm).

A session is read again when it has grown by --regrow (default 25%) since its reading, or when the prompt changed.
Every answer is appended to ~/.relic-extract/report/session-readings.jsonl (never rewritten); relic5-push copies it to
the hub's readings/sessions/<machine>.jsonl. Cache: session-readings-cache-<lane>.json.
"""

import argparse
import hashlib
import json
import os
import queue
import re
import signal
import subprocess
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import duckdb

import days as dy
import readings as rd

HOME = Path.home()
OUT = HOME / ".relic-extract" / "report"
LOG = OUT / "session-readings.jsonl"
KEYS = ("type", "focus", "work", "ended", "open", "repos", "en", "th")
FM_SCHEMA = Path(__file__).with_name("fm-session.schema.json")
EDITS = ("Edit", "Write", "MultiEdit", "NotebookEdit", "apply_patch")
FILE = re.compile(r'"file_path"\s*:\s*"([^"]+)"')
WRAP = re.compile(r"The user sent a new message while you were working:|This is how Claude Code surfaces messages the user "
                  r"sends mid-turn.*?(?:conversation turn\.|$)|Address the message above as you continue this turn\.", re.S)

PROMPT = """You read ONE session of a person's work with an AI coding agent ({engine}, project {project}, {start} .. {end},
{asks} prompts typed by the person, {events} events). Describe what this session was about and did, for the person's
own record. Be concrete: name the project, tools, files and problems you see. Never invent; if the text does not show
it, say less.

Read these right:
- "The user sent a new message while you were working" is the SAME person steering a running agent, never someone else.
- Pasted output (PANE …, rc=…, command output) is the person showing the agent a result.
- The agent's last reply says how the session ended; trust it over the plan in the first prompts.

"type": build = a new feature, app, page or tool · fix = debugging, errors, failing tests · research = reading,
  comparing, exploring · ops = fleet, servers, deploy, machines · writing = books, docs, posts · planning = deciding,
  designing, issues. Use "mixed" ONLY if no kind holds 40%.
"th": two sentences in Thai the way a Thai engineer writes for himself: the topic first, plain verbs, English tech words
  left in English (deploy, test, repo, PR, UI). Never use อย่างไรก็ตาม, ซึ่ง, ในขณะที่, การที่, โดยรวม, นอกจากนี้.

Answer with JSON only, these keys:
{{"type": "build|fix|research|ops|writing|planning|mixed",
  "focus": "what the session was about and did (one sentence, name the project)",
  "work": ["up to 4 short items: what was built, fixed or decided"],
  "ended": "how it ended: done and verified, blocked on what, or left mid-way (one sentence)",
  "open": ["up to 3 things left open at the end; [] if none"],
  "repos": ["the repositories or projects it touched"],
  "en": "two-sentence summary in English",
  "th": "two sentences in Thai"}}

The person's prompts, in order (time Bangkok; long sessions sampled evenly):
{asks_text}

The agent's first reply:
{first_reply}

The agent's last reply:
{last_reply}

Files the agent edited (most edited first): {files}
"""


def one_line(t, width):
    t = " ".join(WRAP.sub(" ", t or "").split())
    return t if len(t) <= width else t[: width - 1] + "…"


def connect(scan, extract):
    con = duckdb.connect()
    con.execute(f"create view s as select * from read_parquet('{scan}/meta/sessions.parquet')")
    con.execute(f"create view x as select * from read_parquet('{extract}/text/*.parquet', union_by_name = true)")
    tools = sorted(Path(extract, "tools").glob("*.parquet"))
    if tools:
        con.execute(f"create view t as select * from read_parquet('{extract}/tools/*.parquet', union_by_name = true)")
    else:
        con.execute("create view t as select null::varchar sid, null::varchar name, null::varchar text where false")
    return con


def sessions(con, a):
    """Main, top-level sessions with at least --min typed prompts, newest first (one row per sid)."""
    where = ["tier = 'main'", "parent_sid is null", "sid is not null", "coalesce(user_text, 0) >= ?"]
    params = [a.min]
    if a.since:
        where.append("last_ts >= ?")
        params.append(a.since)
    if a.until:
        where.append("first_ts <= ?")
        params.append(a.until + "T23:59:59Z" if len(a.until) == 10 else a.until)
    if a.sid:
        where.append("starts_with(sid, ?)")
        params.append(a.sid)
    rows = con.execute(f"""select sid, arg_max(engine, last_ts) engine, arg_max(coalesce(cat, proj), last_ts) project,
                                  min(first_ts) first_ts, max(last_ts) last_ts, max(n_rows) n_rows, max(user_text) asks
                           from s where {' and '.join(where)} group by sid order by last_ts desc""", params).fetchall()
    return [dict(zip(("sid", "engine", "project", "first_ts", "last_ts", "events", "asks"), r)) for r in rows]


def session_input(con, s, max_asks=60):
    rows = con.execute("""select role, ts_th, text from x where sid = ? and chunk = 0 and role in ('user', 'assistant')
                          order by ts, msgkey""", [s["sid"]]).fetchall()
    asks, seen = [], set()
    for role, th, text in rows:
        if role != "user":
            continue
        t = one_line(text, 300)
        if len(t) < 2 or t in seen:
            continue
        seen.add(t)
        asks.append(f"{(th or '')[11:16]} {t}")
    step = max(1, -(-len(asks) // max_asks))
    sample = asks[::step][:max_asks]
    if asks and sample[-1] != asks[-1]:
        sample.append(asks[-1])   # the last thing the person said matters for how it ended
    replies = [t for r, _, t in rows if r == "assistant" and (t or "").strip()]
    files = Counter()
    for (text,) in con.execute(f"select text from t where sid = ? and name in {EDITS}", [s["sid"]]).fetchall():
        files.update(FILE.findall(text or ""))
    return dict(asks_text="\n".join(sample) or "(none)", first_reply=one_line(replies[0], 600) if replies else "(none)",
                last_reply=one_line(replies[-1], 1500) if replies else "(none)",
                files=", ".join(f for f, _ in files.most_common(10)) or "none"), len(asks)


def ask_fm(prompt, host):
    pre = [] if host == "local" else ["ssh", "-o", "BatchMode=yes", host]
    for attempt in range(5):
        cmd = ["fm", "respond", "--no-stream", "--schema", str(FM_SCHEMA)] if not pre else \
            pre + ["NO_COLOR=1 fm respond --no-stream --schema ~/.relic-extract/fm-session.schema.json"]
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=900, env={**os.environ, "NO_COLOR": "1"})
        err = r.stderr or r.stdout
        if r.returncode != 0 and "context size" in err.lower():
            lines = prompt.split("\n")
            body = [i for i, ln in enumerate(lines) if re.match(r"^\d\d:\d\d ", ln)]
            if len(body) <= 2:
                break
            drop = set(body[1::2])
            prompt = "\n".join(ln for i, ln in enumerate(lines) if i not in drop)
            continue
        if r.returncode != 0:
            raise RuntimeError(f"fm on {host}: rc {r.returncode}: {err.strip()[-160:]}")
        got = rd._parse(r.stdout, KEYS)
        return (got | {"json_ok": True, "trimmed": attempt}) if got else {"en": r.stdout.strip()[:600], "json_ok": False}
    raise RuntimeError(f"fm on {host}: still over context after trimming")


def keep(s, model, prompt, ans, secs):
    with open(LOG, "a") as f:
        f.write(json.dumps(dict(at=time.strftime("%Y-%m-%dT%H:%M:%S%z"), sid=s["sid"], model=model, events=s["events"],
                                prompt=hashlib.md5(prompt.encode()).hexdigest()[:12], secs=secs,
                                answer={k: ans.get(k) for k in KEYS if ans.get(k) is not None}), ensure_ascii=False) + "\n")
    LOG.chmod(0o600)


def _stop(*_):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    raise KeyboardInterrupt


def main():
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGHUP, _stop)
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="zai:glm-5.3", help="zai:<model> | gb300:<ollama model> | fm:system")
    ap.add_argument("--workers", type=int, default=8, help="zai: requests at a time")
    ap.add_argument("--fm-hosts", default="local")
    ap.add_argument("--min", type=int, default=3, help="read sessions with at least this many typed prompts")
    ap.add_argument("--since", help="sessions active since (YYYY-MM-DD or ISO, UTC)")
    ap.add_argument("--until")
    ap.add_argument("--sid", help="one session (id prefix)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--regrow", type=float, default=0.25, help="read again once a session grew by this share")
    ap.add_argument("--plan", action="store_true", help="count what a run would read; read none")
    a = ap.parse_args()
    t0 = time.time()
    lane, model = a.model.split(":", 1)
    tag = f"{lane}-{model.replace(':', '_')}"
    con = connect(HOME / ".relic-scan", HOME / ".relic-extract")
    ss = sessions(con, a)
    cache_f = OUT / f"session-readings-cache-{tag}.json"
    cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    todo = []
    for s in ss:   # current: read already, and not grown by --regrow since
        got = cache.get(s["sid"])
        if got and (s["events"] or 0) <= (got.get("events") or 0) * (1 + a.regrow) and got.get("v") == 1:
            continue
        todo.append(s)
    current = len(ss) - len(todo)
    if a.limit:
        todo = todo[: a.limit]
    total = len(todo)
    print(f"session readings: {len(ss):,} sessions (>= {a.min} prompts) · {current:,} current · "
          f"{total:,} to read · {a.model} · {time.time() - t0:.0f}s", flush=True)
    if a.plan or not total:
        return
    fm_free = queue.Queue()
    if lane == "fm":
        for h in [h.strip() for h in a.fm_hosts.split(",") if h.strip()]:
            if h != "local":
                subprocess.run(["ssh", "-o", "BatchMode=yes", h, "mkdir -p ~/.relic-extract && cat > ~/.relic-extract/fm-session.schema.json"],
                               input=FM_SCHEMA.read_text(), text=True, check=True, timeout=60)
            fm_free.put(h)
    tun = dy.tunnel(dy.OLLAMA_HOST, model) if lane == "gb300" else None
    lock, done, t_start = threading.Lock(), [0], time.time()

    def one(s):
        with lock:   # duckdb connections are not shared across threads: one cursor per call
            c = con.cursor()
        inp, n = session_input(c, s)
        prompt = PROMPT.format(engine=s["engine"] or "?", project=s["project"] or "?", start=(s["first_ts"] or "")[:16],
                               end=(s["last_ts"] or "")[:16], asks=n, events=s["events"], **inp)
        t1 = time.time()
        if lane == "zai":
            ans = rd.ask_zai(model, prompt, KEYS)
        elif lane == "fm":
            host = fm_free.get()
            try:
                ans = ask_fm(prompt, host)
            finally:
                fm_free.put(host)
        else:
            ans = dy.ask(model, prompt, keys=KEYS)
        secs = round(time.time() - t1, 1)
        if ans.get("json_ok"):
            keep(s, a.model, prompt, ans, secs)
        return s, ans, secs

    workers = a.workers if lane == "zai" else fm_free.qsize() if lane == "fm" else 1
    ex = ThreadPoolExecutor(max_workers=max(1, workers))
    try:
        futs = [ex.submit(one, s) for s in todo]
        for f in as_completed(futs):
            try:
                s, ans, secs = f.result()
            except Exception as e:
                print(f"  failed: {e.__class__.__name__}: {str(e)[:120]}", flush=True)
                continue
            with lock:
                done[0] += 1
                if ans.get("json_ok"):
                    cache[s["sid"]] = {"v": 1, "events": s["events"], "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "focus": ans.get("focus")}
                el = time.time() - t_start
                rate = done[0] / el if el else 0
                left = (total - done[0]) / rate if rate else 0
                eta = time.strftime("%H:%M", time.localtime(time.time() + left))
                print(f"  [{done[0]}/{total} {100 * done[0] / total:.0f}% · {rate * 60:.1f}/min · {left / 60:.0f} min left · ETA {eta}] "
                      f"{s['sid'][:8]} {s['project'] or ''} · {secs}s · {'' if ans.get('json_ok') else 'NO JSON · '}{str(ans.get('focus'))[:70]}",
                      flush=True)
                if done[0] % 25 == 0:
                    cache_f.write_text(json.dumps(cache, ensure_ascii=False))
    finally:
        ex.shutdown(wait=False, cancel_futures=True)
        cache_f.write_text(json.dumps(cache, ensure_ascii=False))
        cache_f.chmod(0o600)
        dy._TUN.clear()
        if tun:
            tun.terminate()
    print(f"session readings: {done[0]:,} read · {time.time() - t0:.0f}s -> {LOG}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("session readings: stopped, cache saved; the next run resumes from it", flush=True)
        raise SystemExit(130)
