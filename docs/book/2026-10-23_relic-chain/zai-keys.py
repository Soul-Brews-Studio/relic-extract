#!/usr/bin/env python3
"""Is any z.ai key expired? One tiny request per `pass` entry; prints the entry name, HTTP status and z.ai's
error code, never the key.
    python3 zai-keys.py glm/zai-2 glm/zai-3 glm/nat-wrw"""
import json, re, subprocess, sys, urllib.error, urllib.request

for entry in sys.argv[1:]:
    key = subprocess.run(["pass", "show", entry], capture_output=True, text=True).stdout.split("\n")[0].strip()
    body = json.dumps({"model": "glm-5.3", "max_tokens": 64, "messages": [{"role": "user", "content": "ok"}]}).encode()
    req = urllib.request.Request("https://api.z.ai/api/anthropic/v1/messages", body,
                                 {"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            print(f"{entry:<12} HTTP {r.status}  ok")
    except urllib.error.HTTPError as e:
        t = e.read().decode("utf-8", "replace")
        code = re.search(r'"code":\s*"?(\d+)', t)
        msg = re.search(r'"message":\s*"([^"]{0,60})', t)
        print(f"{entry:<12} HTTP {e.code}  code {code.group(1) if code else '-'}  {msg.group(1) if msg else ''}")
