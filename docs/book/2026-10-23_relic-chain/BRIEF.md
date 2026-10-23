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
