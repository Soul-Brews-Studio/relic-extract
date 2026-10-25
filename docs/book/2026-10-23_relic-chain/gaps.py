"""Pauses longer than 30 s between two answers of one lane in readings.jsonl, on one day: where the lane stalled."""
import json
import os
import sys
from datetime import datetime

lane, day = sys.argv[1], sys.argv[2]   # e.g. gb300 2026-10-24
prev = None
n = 0
for line in open(os.path.expanduser("~/.relic-extract/report/readings.jsonl")):
    try:
        r = json.loads(line)
    except ValueError:
        continue
    if not r["model"].startswith(lane) or not r["at"].startswith(day):
        continue
    n += 1
    at = datetime.strptime(r["at"], "%Y-%m-%dT%H:%M:%S%z")
    if prev and (at - prev).total_seconds() > 30:
        print(f"  pause {prev:%H:%M:%S} -> {at:%H:%M:%S}  ({(at - prev).total_seconds():.0f} s)  next window {r['unit']}")
    prev = at
print(f"{n:,} answers from {lane} on {day}")
