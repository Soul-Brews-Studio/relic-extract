"""Print what one of this session's own Bash calls printed, as it came back (the transcript keeps every tool result).
    python3 toolout.py <session.jsonl> <text in the command> [n-th match, default 1] [max lines, default 40]
The first line printed is the time the result arrived (UTC, as the transcript stores it)."""
import json
import sys

path, pat = sys.argv[1], sys.argv[2]
nth = int(sys.argv[3]) if len(sys.argv) > 3 else 1
cap = int(sys.argv[4]) if len(sys.argv) > 4 else 40
want, seen = {}, 0
for line in open(path):
    try:
        r = json.loads(line)
    except ValueError:
        continue
    c = (r.get("message") or {}).get("content")
    if not isinstance(c, list) or not r.get("timestamp"):  # a copy without a timestamp (progress rows) is skipped
        continue
    for x in c:
        if not isinstance(x, dict):
            continue
        if x.get("type") == "tool_use" and pat in str((x.get("input") or {}).get("command", "")):
            want[x["id"]] = True
        elif x.get("type") == "tool_result" and x.get("tool_use_id") in want:
            seen += 1
            if seen != nth:
                continue
            body = x.get("content")
            txt = body if isinstance(body, str) else "\n".join(b.get("text", "") for b in body if isinstance(b, dict))
            print(f"-- arrived {r.get('timestamp', '')[:19]}Z")
            print("\n".join(txt.splitlines()[:cap]))
            sys.exit(0)
sys.exit(f"no result #{nth} for a command containing {pat!r}")
