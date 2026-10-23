# BRIEF — shared by every chapter writer

Book dir (absolute): `{{BOOK_DIR}}`
Read `OUTLINE.md` there first: title, parts, and YOUR chapter's subtopics and image list.

## What this book is
{{ONE PARAGRAPH: what the tool is, that every command was run for real on {{DATE}} on {{MACHINE}},
that outputs are in `captures/NN-slug.txt` rendered as `images/NN-slug.png`, diagram cards in
`diagrams/Dn-*.txt` → `images/Dn-*.png`, author = <oracle> (an AI) with <human>.}}

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
{{LIST: D1-… D2-… ; 00-help 01-… 02-… …}}

## FACTS measured on {{DATE}} (use these; do not add others)
{{BULLETS — every measured number the prose may use that is not visible in a capture, each with
where it was measured. If it cannot be measured, it does not go in the book.}}
