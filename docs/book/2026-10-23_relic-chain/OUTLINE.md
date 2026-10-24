---
title: "หนึ่งปีในหน้าเดียว"
subtitle: "relic-scan → relic-extract → gb300 → รายงานทีละเดือน ทีละวัน"
tagline: "ทุกคำสั่งรันจริง ทุก capture คือเทอร์มินัลจริง ยกเว้นภาพปกที่ AI วาด — 2026-10-23"
author: relic-extract (AI) · กับ Nat
date: 2026-10-23
language: Thai (kien-thai 7 frames + nat-thai dev register) — commands/flags stay English
style: /browser-tutorial — numbered steps, image under the command that produced it
images: every image rendered from text by /ascii-diagram --png (captures/ + diagrams/), plus page screenshots (shots/)
target: 8 chapters, ~60-80 pages
image budget: >= 1 image per expected page
parts: 3
---

## 00 คำนำ — วิธีอ่านเล่มนี้  (images: D1-chain)
- what the chain is (one diagram), where every image comes from, the kicker เขียนโดย AI เพื่อ AI
proof: D1 (numbers from captures 05, 11, 21, 91)

## ภาค 1 — ข้อมูล: จาก transcript ถึง chunk

### บทที่ 1: relic-scan — เครื่องนี้มีอะไร  (images: 01-scan-help, 02-scan-dry, 03-scan-log, 04-scan-files, 05-scan-count)
- 1.1 help: the commands
- 1.2 run --dry-run: what an index would read, writes nothing
- 1.3 log: every index and check
- 1.4 the files it leaves: months + meta
- 1.5 count everything first, by what each row is
proof: captures 01-05

### บทที่ 2: relic-extract — ตัด ล้าง ใส่ key  (images: 10-config, 11-status, 12-analyse, 13-whatif, 14-run, 15-parts, 16-schema, 17-config-clean)
- 2.1 config: one file for the chain (~/.arra/relic.toml)
- 2.2 status: three streams
- 2.3 analyse: what the clean step drops, before writing anything
- 2.4 --what-if: try a setting first
- 2.5 run: only what changed
- 2.6 the parts and _extract.json (the finished marker)
- 2.7 one chunk row: key = blake2b of the text
- 2.8 the clean rules in the TOML
proof: captures 10-17

### บทที่ 3: embed บน gb300  (images: 20-gb300, 21-cache, 22-embed-meta, 23-embed-again)
- 3.1 the GPU host
- 3.2 the vector cache and the LanceDB tables: sizes
- 3.3 one stream's _meta.json: how long it took
- 3.4 run it again: nothing to embed, every key in the cache
proof: captures 20-23

## ภาค 2 — อ่าน: ค้น จัดกลุ่ม และวัด

### บทที่ 4: ค้น — ของเรากับ relic3  (images: 30-search-fused, 31-search-file, 32-relic3-file, 33-relic3-sem)
- 4.1 one question over text, thinking, tools and vaults, fused
- 4.2 an exact file name: ours finds it
- 4.3 relic3 on the same name: no match
- 4.4 relic3 --semantic on a question
proof: captures 30-33

### บทที่ 5: จากตัวเลขเป็นหน้า  (images: 40-topics, 41-work, 42-oracles, 43-memory, 44-build, 45-jsdom, S1-page, S2-page, S3-page, S4-page, S5-page)
- 5.1 topics: k-means on 140k prompt vectors, names by hand
- 5.2 did the work land: prompts vs commits vs notes
- 5.3 oracles: born, for what, how long
- 5.4 memory: does the vault know what was asked
- 5.5 build the page, three views
- 5.6 check every view with jsdom
- 5.7 the page itself (screenshots)
proof: captures 40-45, shots S1-S3

### บทที่ 6: อ่านทีละวันด้วย model บน gb300  (images: 50-models, 51-compare, 52-day-reading, 53-readings-log)
- 6.1 which models gb300 has
- 6.2 four models, the same 12 days, scored
- 6.3 one day as qwen3:14b read it
- 6.4 every answer kept: readings.jsonl
proof: captures 50-53

## ภาค 3 — ส่ง และสิ่งที่พัง

### บทที่ 7: publish  (images: 60-publish, 61-live, 90-just-list)
- 7.1 just publish: build the share view, gitleaks, deploy
- 7.2 the live page answers
- 7.3 every recipe
proof: captures 60, 61, 90

### บทที่ 8: สิ่งที่พัง และกฎที่ได้  (images: D2-broke, 91-sizes, 92-git-log)
- the real failures of the day, each: what happened · how it was noticed · cause · fix · rule
  (DuckDB reserved aliases; port 11435 was the ANE embed server; a fixed cosine 0.80 gave ~0%; ego scripts with
  node:fs printed nothing; an ssh drop killed a blocking pull; v1 day readings said "several projects")
proof: D2 (from the session's own errors), captures 91, 92

## ภาค 4 — วันที่สอง (2026-10-24): อ่านละเอียดขึ้น เทียบสองโมเดล และงานที่ต้องรอดข้ามคืน

### บทที่ 9: อ่านทีละช่วง — 3 ชั่วโมง 1 ชั่วโมง 15 นาที  (images: 100-readings-help, 101-blocks-3h, 102-blocks-1h, 103-prompt-15m, 104-deep-keys, 105-deep-reading, 106-window-row, 107-progress, S6-page)
- 9.1 readings.py: one script, four grains (day, 3h, 1h, 15m), two hosts (gb300, z.ai), --deep adds friction + lesson
- 9.2 the 3-hour lane and the 1-hour lane, as their panes reported (blocks.py)
- 9.3 "The day was focused on…" in a 15-minute reading: the day prompt leaked; the 15m prompt says "these 15 minutes"
- 9.4 --deep: friction and lesson (and the bug: the gb300 path kept only the day keys — see chapter 12)
- 9.5 one 15-minute window read deep
- 9.6 every window leads back to its sessions: session ids on the page (private view only)
- 9.7 how far the lanes are (progress.py) + the grid on the page (S6)
proof: captures 100-107, shot S6

### บทที่ 10: สองโมเดล อ่านช่วงเดียวกัน  (images: D3-lanes, 110-build-report, 111-lanes-table, 112-lanes-agree, 113-lane-speed, S7-page)
- 10.1 the lanes (diagram): which model read which grain, how fast
- 10.2 build the page with every lane
- 10.3 the table: type mix per lane, how often the day's top project leads a window, projects leading a day
- 10.4 one rule for "leads": the table and the paragraph used two definitions (50%/3.06 vs 51%/3.32); now one
- 10.5 same windows, two models: they agree on half the days; gb300 says build where z.ai says mixed
- 10.6 seconds per answer: gb300 one at a time vs z.ai 4 workers
- 10.7 the table on the page (S7)
proof: D3, captures 110-113, shot S7

### บทที่ 11: พูดหรือพิมพ์ — model จาก Wispr Flow  (images: D4-stt, 120-wispr, 121-stt-ngram, 122-stt-export, 123-stt-train, 128-stt-metrics, 124-stt-scores, 126-stt-rescore, 127-stt-rescore-sh, 125-stt-projects)
- 11.1 the idea (diagram): Wispr Flow's own history labels which prompts were spoken; a model guesses the rest
- 11.2 the labels: Wispr's history, read-only, counts only
- 11.3 a char n-gram model, 5-fold CV: AUC high, AP low (a 1:200 base rate)
- 11.4 train on gb300: bge-m3 fine-tuned, 30 typed per spoken, the epoch with the best AP kept
- 11.5 held out: fine-tuned vs n-gram on the same split
- 11.6 the data doubled under the model: 41k prompts with no score; --score-only rescored them, no retraining
- 11.7 the year scored: which months, which projects; June-July read as spoken before Wispr was installed on m5
proof: D4, captures 120-127

### บทที่ 12: งานยาวข้ามคืน — สิ่งที่พังในวันที่สอง  (images: D5-overnight, 130-refused, 131-tunnel-code, 132-gaps, 133-cycle, 134-kill-save, 135-kill-test, 136-scan-sessions, 139-scan-message, 140-merge-message, 141-scan-log, 142-scan-tiers, 143-rerun-slip, 137-tz, 138-git-log2)
- each failure: what happened · how it was noticed · cause · fix · rule
- 12.1 the ssh tunnel died after 825 windows: Connection refused → ServerAlive + reopen + autossh
- 12.2 the reopen worked by itself at 13:18 (a 58 s pause in readings.jsonl)
- 12.3 23:00-08:00 for three nights: the cycle script, and GMT+7
- 12.4 a kill that did not save: the with-block waited for every queued window; SIGHUP from the pane; the fix and the test
- 12.5 deep readings without friction: 8,400 windows saved without the two keys; read again
- 12.6 the scan index shrank to 3,048 sessions (a setup script run in the wrong account); relic4-scan restored it; the kept copy is the bad file
- 12.7 then it doubled: every .claude home merged (101,183 sessions) — every lane re-queued, unchanged windows kept by prompt hash
- 12.8 my own slip: a generated capture script re-ran the whole book's captures and a publish
- 12.9 the day's commits
proof: D5, captures 130-143
