"""Print what a herdr pane sent back to this session (the /herdr-pane-run report), as it arrived.
    python3 paneout.py <session.jsonl> <pattern>     # pattern: "PANE w12:p14" or "Connection refused"
Dropped: the direnv export line, the shell prompt (it carries an account name) and the echoed pane command."""
import json
import sys

path, pat = sys.argv[1], sys.argv[2]
for line in open(path):
    try:
        r = json.loads(line)
    except ValueError:
        continue
    if r.get("type") == "user":
        c = r["message"]["content"]
    elif isinstance(r.get("content"), str):  # a message typed while a turn ran is queued first, outside "user"
        c = r["content"]
    else:
        continue
    txt = c if isinstance(c, str) else "\n".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
    if pat not in txt:
        continue
    print(f"-- arrived {r.get('timestamp', '')[:19]}Z")
    i = txt.find(pat)
    for ln in txt[txt.rfind("\n", 0, i) + 1:].splitlines()[:40]:
        if ln.startswith(("direnv:", "<", "∙", "Installed ")) or "pasted_content" in ln or "system-reminder" in ln or "☁" in ln:
            continue
        print(ln)
    if len(sys.argv) < 4:
        break
