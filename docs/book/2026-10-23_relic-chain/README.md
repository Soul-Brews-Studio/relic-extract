# {{TITLE}}

**{{SUBTITLE}}**

ทุกคำสั่งรันจริง ทุกภาพในเล่มคือเทอร์มินัลจริง ยกเว้นภาพปกที่ AI วาด — {{DATE}} · เขียนโดย {{ORACLE}} (AI) กับ {{HUMAN}}

![{{what D1 shows}}](images/D1-architecture.png)

| | บท |
|---|---|
| | [คำนำ](00-frontmatter.md) |
| ภาค 1 | [1. ...](01-....md) |

PDF: `book.pdf` (build with `make pdf`).

## How this book was made (/oracle-write-proof-book)
- `capture.sh` ran every command for real and kept the output verbatim in `captures/`.
- `cards.py` + `/ascii-diagram --png` rendered each capture to `images/NN-slug.png`; diagram cards
  in `diagrams/*.txt` became `images/Dn-*.png`. The text files are the source of truth.
- Chapters drafted in parallel from `BRIEF.md` + `OUTLINE.md`, reviewed 3 ways, fixed per `FIX-RULES.md`.
- `make pdf` → PyThaiNLP → pandoc → fixdash → imgwidth → typst 0.15.1 · `make check` gates.

## Cover art
`images/cover-art.jpg` is AI-generated (Codex `codex exec`, via `scripts/make-cover-art.sh`; subject: {{COVER SUBJECT}}). It is not a photograph and not a capture.
