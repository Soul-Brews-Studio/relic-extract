# BRIEF — shared by every chapter writer

Book dir (absolute): `/opt/Code/github.com/Soul-Brews-Studio/relic-extract/docs/book/2026-10-23_relic-chain`
Read `OUTLINE.md` there first: title, parts, and YOUR chapter's subtopics and image list.

## What this book is
The relic chain on one Mac (m5): relic-scan finds and indexes every AI-agent transcript, relic-extract picks,
cleans and cuts the text into chunks keyed by blake2b, relic4 embeds them on the gb300 GPU, and `report/` turns it
all into one month-by-month, day-by-day page (published as a share view at relic.buildwithoracle.com/report).
Every command was run for real on 2026-10-23 on m5; outputs are in `captures/NN-slug.txt` rendered as
`images/NN-slug.png`; diagram cards in `diagrams/Dn-*.txt` → `images/Dn-*.png`; page screenshots of the live page
(Thai view) are `images/S1-page.jpg` … `S5-page.jpg` (taken with ego-browser). Author: relic-extract (an AI,
Claude) with Nat. Kicker: เขียนโดย AI เพื่อ AI. Register: nat-thai dev mode (ผม/เรา sparingly, ครับ light in dense
parts, claim + command + output first), kien-thai frames.

## Style = /browser-tutorial, in Thai
- Numbered steps inside each section: `### ขั้นที่ N — <what it does>`, N restarting at 1 per `##`.
  Each step: 1–3 sentences telling the reader what to type and why → the command in a ```bash block
  → the image of the REAL output directly under it → 1–3 sentences reading the output.
- **Prose carries the instruction; the image confirms it.** A reader with no images must still
  follow. Quote the 2–6 most important output lines in a plain ``` block when the point is a number.
- Image: `![<what is IN the shot, Thai ok>](images/NN-slug.png)` — relative path, only names that
  exist in `images/` (list below). Never invent an image name.
- In each step, the ONE key idea in **bold** — one span per step.
- When something fails or surprises, that IS the lesson: keep it, explain the cause, give the fix.
- Diagram cards go where the concept is introduced, with one sentence on what the picture shows
  that prose did not.
- **Pace: every printed page carries 1–2 images (3 when all three are small captures).** In
  practice: no more than ~250 Thai words (or one long code block) between two images. Pair short
  captures in one step. A section that would be prose-only gets the capture behind its main claim,
  or is cut. `make check` fails on a text-only page (`page_images.py`).

## Language — Thai, kien-thai frames
Natural Thai for a developer colleague next to the terminal. Commands, flags, file names, code,
numbers and product names stay in English/ASCII. f1 topic-comment · f2 condition first (พอ...ก็...)
· f3 short clauses · f4 particles where natural · f5 drop pronouns the context carries · f6 ก็ as
rhythm · f7 pivot with a question or แต่. No English sentences in prose. No emoji. No "!!!".

## Hard rules
- **Never invent output, numbers, flags or behaviour.** Every number must appear in a capture file
  or in FACTS below. Open the capture `.txt` files and read them.
- ```bash for commands, untagged for output. Lines ≤ 76 chars (wrap with ` \`, cut output with `…`);
  verbatim source excerpts stay verbatim.
- Paragraphs ≤ ~500 characters.
- File starts `# บทที่ N: <title>` (frontmatter `# คำนำ`). Sections `##`, steps `###`.
- End with a short forward hook — no recap list.
- Read your captures with ONE call: `python3 verify.py --bundle <your-chapter>.md` (prints every capture and
  diagram the OUTLINE lists for you). Never open a PNG. Never run make, typst or pdftoppm: the lead builds.
  Stop at ~60 tool calls. `python3 verify.py` (0.1 s) checks your numbers, ids and times against the captures.
- **WRITE THE FILE YOURSELF**. Return ONLY: `wrote NN-slug.md — <words> words, <n> images`.

## Images available (exact names)
00-help.png 01-scan-help.png 02-scan-dry.png 03-scan-log.png 04-scan-files.png 05-scan-count.png 10-config.png 11-status.png 12-analyse.png 13-whatif.png 14-run.png 15-parts.png 16-schema.png 17-config-clean.png 20-gb300.png 21-cache.png 22-embed-meta.png 23-embed-again.png 30-search-fused.png 31-search-file.png 32-relic3-file.png 33-relic3-sem.png 40-topics.png 41-work.png 42-oracles.png 43-memory.png 44-build.png 45-jsdom.png 50-models.png 51-compare.png 52-day-reading.png 53-readings-log.png 60-publish.png 61-live.png 90-just-list.png 91-sizes.png 92-git-log.png D1-chain.png D2-broke.png S1-page.jpg S2-page.jpg S3-page.jpg S4-page.jpg S5-page.jpg

## FACTS measured on 2026-10-23 (use these; do not add others)
- Fresh embed on gb300, text: 748,619 distinct texts in 785.2 s (953 texts/s including transfer); the whole first
  chain (scan + extract + embed) took 833 s. Source: the pane log `== chain done in 833s` and `embed: gb300 done in 785.2s`.
- Fresh embed, tools: 1,613,924 texts in 1,733.0 s (17 shards); thinking 99,926 texts; vault 77,278 texts in 275.6 s.
- The clean step dropped, on the live index (after today's rules): 213,661 messages (relic-extract run, 2026-10-23 21:04).
- Model comparison (12 busiest-of-month days, same prompt, names normalised): qwen3:14b names 0.54 · generic 0.08 ·
  3.3 s/day; typhoon2.1-gemma3-12b names 0.54 · generic 0.25 · 4.0 s; qwen3:30b-a3b names 0.29 · 1.9 s;
  typhoon-judtem-v5 names 0.00 (it invented a "customer", ลูกค้า). qwen3:14b was chosen.
- Day readings: 329 days, 326 read by qwen3:14b in 1,104 s (v3 prompt). v2 → v3: Thai AI-tell words in 36 → 19 days;
  type "mixed" 275 → 12 days (then "build" 260: the type field is still weak).
- z.ai (glm-5.3) as a second lane: about 30-70 s per window with thinking; 24 parallel workers hit HTTP 429.
- Attention (switches.py, no model): 156,853 main-session prompts, 53% land in a different project from the one before;
  median run 1 prompt; median projects in the same hour peaked at 6 (2026-07).
- relic3 against ours: an exact file name (semantics_14_umap_map) — relic3 0 matches across 53 weeks, ours 3 hits.
- Screenshots: ego-browser's node prints to stderr, not stdout; scripts that imported node:fs printed nothing.
- z.ai keys checked one by one (captures 93, 94): glm/zai-2 gave 1302 (rate limit) and later 200; glm/zai-3 gave
  HTTP 429 with code 1113 (insufficient balance), so readings.py drops a key that answers 1113; glm/nat-wrw 200.
  The z.ai lane was restarted with 4 workers.
- relic5's [extract] after command first failed with exit 75 (capture 93: "after: exited 75"); relic5 changed it to
  `index --wait`. z.ai 1210: glm-5.3 rejects `thinking: disabled`. readings.py waits on retry-after for a 429.

## Part 4 (chapters 9-12): the second day, 2026-10-24
Same rules. Captures 100-139 were run on 2026-10-24 by `capture2.sh` (same `run`/`runsh` format). Some captures
print a pane's report as it arrived in this session (`paneout.py <session> <pattern>`): say so — "as the pane
reported" — never present them as run again. Screenshots S6-page.jpg (the 1-hour grid) and S7-page.jpg (the lane
table) are the private page on 127.0.0.1, taken with ego-browser.

Images for part 4 (exact names): 140-merge-message.png 141-scan-log.png 142-scan-tiers.png 143-rerun-slip.png 100-readings-help.png 101-blocks-3h.png 102-blocks-1h.png 103-prompt-15m.png
104-deep-keys.png 105-deep-reading.png 106-window-row.png 107-progress.png 108-lane-restart.png 110-build-report.png
111-lanes-table.png 112-lanes-agree.png 113-lane-speed.png 120-wispr.png 121-stt-ngram.png 122-stt-export.png
123-stt-train.png 128-stt-metrics.png 124-stt-scores.png 126-stt-rescore.png 127-stt-rescore-sh.png 125-stt-projects.png 130-refused.png 131-tunnel-code.png 132-gaps.png
133-cycle.png 134-kill-save.png 135-kill-test.png 136-scan-sessions.png 137-tz.png 138-git-log2.png
139-scan-message.png D3-lanes.png D4-stt.png D5-overnight.png S6-page.jpg S7-page.jpg

### FACTS for part 4 (2026-10-24, times +07 = GMT+7, Asia/Bangkok)
- Nat's asks, in his words: "make autossh ?" · "now please run for 3days and stop and resume at 23:00" (answer chosen:
  start now, stop 08:00, resume 23:00) · "can you create a model that show which prompt from STT / transcription?" ·
  "can we train a model?" · "every our result do we know the seesion id?" (→ session ids on every window row).
- The 15-minute gb300 lane's first run lost its ssh tunnel after its answer at 03:31:46 (capture 132) and then
  failed every window (pane: Errno 61 Connection refused, 3 retries each); Nat pasted that pane at 08:05. Fix cdec387 (08:06): ServerAlive + `_reopen()` after a retry; ed600e7
  (09:13): autossh when installed. The lane restarted 08:28:15 (ps) on the 08:06 code (plain ssh + reopen).
- At 13:18:02 that run opened a new ssh tunnel by itself (ps start time of the ssh process); readings.jsonl shows
  the 58 s pause 13:17:09 → 13:18:07 (capture 132). No window was lost.
- 14:3x: the deep lane's cache held 8,400 windows and none had friction or lesson: `days.ask()` (the gb300 path)
  returned only the 8 day keys; z.ai's `ask_zai()` kept all keys. Fixed in 32368be; a cached deep window without
  friction is read again, so all 15,141 windows are read (the window count grew from 13,725 at 08:28 to 15,141 at
  14:35: relic-scan's restored index and the day's new prompts).
- The same stop showed the SIGTERM save (afbc26e, 08:26) did not work: the last windows printed (up to 2026-07-20
  08:15) were not in the cache (it ended at 2026-07-19 18:00). Cause: the loop ran inside `with ThreadPoolExecutor`,
  whose exit waits for every queued window before `finally`; the pane closing then sent SIGHUP. Fix 32368be: no
  with-block, `shutdown(wait=False, cancel_futures=True)`, SIGHUP handled, the reopen table cleared on stop.
  Test (capture 135): TERM after 15 s → 4 windows printed, 4 in the cache with friction, no tunnel left.
- 08:11: relic-scan's meta/sessions.parquet was rewritten with 3,048 sessions; the page's repo chart dropped (monthly
  repo values 1,386 → 1,204). Found by diffing two report.json builds; reported to relic4-scan (pane w11:p1), which
  restored it at 08:15 (capture 139). The kept copy ~/.relic-scan.before-nat-incident-2026-10-24 is the bad 08:11
  index itself (3,048 sessions, capture 136), kept as-is — not the old good one (relic4-scan, capture 140).
- 13:52 and 14:34: relic4-scan merged every other .claude home into the index (black's 17 GB home, white, mba, in-home
  projects-* folders, neo archives) and Nat's own transcripts via /Users/Shared/nat-export; "settled now, from here it
  only grows with live use" (capture 140). Sessions 49,774 → 101,183 (capture 136); main-tier prompts seen by stt.py
  210,866 → 284,840 (captures 121, 124). Every lane read before the merge was re-queued: gb300 15m → day → 3h → 1h
  (/tmp/relic-gb-queue.sh, pane w12:p17, same 08:00 stop / 23:00 resume) and the z.ai lane (pane w12:p18).
  A window whose prompts did not change keeps its cached reading (cache key = prompt hash).
- My own slip, 14:4x: capture2.sh was built from capture.sh with a sed range whose end marker never matched, so it
  carried all of part 1-3's commands: its 39 captures were re-run, 29 came out different and were overwritten (restored from git; those 29
  kept in /tmp/bk/captures-rerun-1024), `relic-extract run --no-after` ran, and `just publish` deployed the share view
  (gitleaks: no leaks; 1,386 monthly values — the full data). Rule: read a generated script before running it.
- "The day's top project leads": the lane table pooled windows (3h 50% / 3.06 projects a day) while the paragraph used
  blocks.py's per-day average (51% / 3.32). Commit f8ed5bf: one rule everywhere (days with 3+ windows, each day's
  share averaged, windows with no project left out).
- STT: Wispr Flow's history is opened read-only; prompt text and dictation text are never printed in this book.
  stt.py's matching rule: a dictation counts when a prompt was sent from 30 s before to 20 min after it and
  rapidfuzz partial_ratio ≥ 85. Negatives: main-tier prompts in the Wispr weeks with no dictation behind them.
  The bge-m3 fine-tune ran on gb300 (NVIDIA GB300, CUDA 13.2) in 182 s.
- After the merge, stt.py --scores (capture 124) found fine-tuned scores for only 159,411 of 200,711 prompts: the
  new prompts had no score and counted as typed (9,213 spoken). stt_train.py got --score-only (the kept model, no
  retraining); stt-rescore.sh ran export -> gb300 -> stt.py: 9,665 of 200,757 read as spoken, labels 271 spoken /
  55,678 typed, the model still the one trained on 263 labels (capture 126). Commit: stt_train --score-only.
- Session 008db2b3 (in capture 106 and the page's rows) is this session: relic-extract, the agent writing this book.
  Session ids are on window rows in the private view only; build.py leaves them out of the share and public views.
- z.ai lanes ran with 4 workers (the 1-hour pass while this was written); gb300 reads one window at a time.
