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

## 00 คำนำ — วิธีอ่านเล่มนี้  (images: D1)
- what the chain is (one diagram), where every image comes from, the kicker เขียนโดย AI เพื่อ AI
proof: D1 (numbers from captures 05, 11, 21, 91)

## ภาค 1 — ข้อมูล: จาก transcript ถึง chunk

### บทที่ 1: relic-scan — เครื่องนี้มีอะไร  (images: 01, 02, 03, 04, 05)
- 1.1 help: the commands
- 1.2 run --dry-run: what an index would read, writes nothing
- 1.3 log: every index and check
- 1.4 the files it leaves: months + meta
- 1.5 count everything first, by what each row is
proof: captures 01-05

### บทที่ 2: relic-extract — ตัด ล้าง ใส่ key  (images: 10, 11, 12, 13, 14, 15, 16, 17)
- 2.1 config: one file for the chain (~/.arra/relic.toml)
- 2.2 status: three streams
- 2.3 analyse: what the clean step drops, before writing anything
- 2.4 --what-if: try a setting first
- 2.5 run: only what changed
- 2.6 the parts and _extract.json (the finished marker)
- 2.7 one chunk row: key = blake2b of the text
- 2.8 the clean rules in the TOML
proof: captures 10-17

### บทที่ 3: embed บน gb300  (images: 20, 21, 22, 23)
- 3.1 the GPU host
- 3.2 the vector cache and the LanceDB tables: sizes
- 3.3 one stream's _meta.json: how long it took
- 3.4 run it again: nothing to embed, every key in the cache
proof: captures 20-23

## ภาค 2 — อ่าน: ค้น จัดกลุ่ม และวัด

### บทที่ 4: ค้น — ของเรากับ relic3  (images: 30, 31, 32, 33)
- 4.1 one question over text, thinking, tools and vaults, fused
- 4.2 an exact file name: ours finds it
- 4.3 relic3 on the same name: no match
- 4.4 relic3 --semantic on a question
proof: captures 30-33

### บทที่ 5: จากตัวเลขเป็นหน้า  (images: 40, 41, 42, 43, 44, 45, S1, S2, S3)
- 5.1 topics: k-means on 140k prompt vectors, names by hand
- 5.2 did the work land: prompts vs commits vs notes
- 5.3 oracles: born, for what, how long
- 5.4 memory: does the vault know what was asked
- 5.5 build the page, three views
- 5.6 check every view with jsdom
- 5.7 the page itself (screenshots)
proof: captures 40-45, shots S1-S3

### บทที่ 6: อ่านทีละวันด้วย model บน gb300  (images: 50, 51, 52, 53)
- 6.1 which models gb300 has
- 6.2 four models, the same 12 days, scored
- 6.3 one day as qwen3:14b read it
- 6.4 every answer kept: readings.jsonl
proof: captures 50-53

## ภาค 3 — ส่ง และสิ่งที่พัง

### บทที่ 7: publish  (images: 60, 61, 90)
- 7.1 just publish: build the share view, gitleaks, deploy
- 7.2 the live page answers
- 7.3 every recipe
proof: captures 60, 61, 90

### บทที่ 8: สิ่งที่พัง และกฎที่ได้  (images: D2, 91, 92)
- the real failures of the day, each: what happened · how it was noticed · cause · fix · rule
  (DuckDB reserved aliases; port 11435 was the ANE embed server; a fixed cosine 0.80 gave ~0%; ego scripts with
  node:fs printed nothing; an ssh drop killed a blocking pull; v1 day readings said "several projects")
proof: D2 (from the session's own errors), captures 91, 92
