# FIX-RULES — shared by every chapter fixer

Apply, to YOUR chapter file only, every finding that names your file in:
REVIEW-facts.md, REVIEW-codeblocks.md, REVIEW-formatting.md. Plus these book-wide decisions:

1. Step headings: exactly `### ขั้นที่ N — <what the step does>`, N restarting at 1 in each `##`.
   A case-study chapter may use `### กรณีที่ N — ...`.
2. Bold: in each step, the ONE key idea in **bold** — 1 span per step. No bold inside code.
3. Paragraphs: split any prose paragraph over ~500 characters at a natural idea boundary.
4. Code widths: bash ≤ 76 chars (wrap ` \` + 2-space continuation); output ≤ 76 (cut with `…`).
   Verbatim source excerpts stay verbatim — typst wraps them.
5. Provenance: a "not in any capture" finding is resolved by CITING the capture that the lead
   added for it (93-errors, 94-zai-keys; plus BRIEF.md FACTS), never by inventing a source. If no capture exists,
   remove or soften the claim.
6. Cross-chapter duplication: ch5 keeps how the page is built, ch6 the model readings, ch8 every failure; others point back in one clause.
7. Never add a number, flag or output line that is not in captures/*.txt or BRIEF.md FACTS.
8. Keep every image and path unless a finding says it is wrong; each sits directly under the
   command that produced it.
9. Thai register as BRIEF.md. No emoji. No English sentences in prose.
10. Image pace: if `make check` lists a page of YOUR chapter as text-only, fix it in this order —
    pull the next image up (shorten the prose above it), pair two small captures in one step, add
    the existing capture that backs a claim on that page, or trim prose. Never add an image that
    is not in images/, never add a decorative image.
11. Code tags: a block that uses a zsh builtin (`print`, `&!`) is tagged ```zsh, not ```bash.
12. Wrap a command only with the shell's own joins: between arguments with ` \`; inside one quoted string
    with `'…'\` then `'…'` at column 0 of the next line; inside a path with `\` then the rest at column 0.
    Anything else changes the command. An unbreakable token may run past 76 columns.
13. Never run make, typst or pdftoppm: the lead builds after all fixers finish.
14. A finding whose quoted text is not in the current file is stale: skip it and say "text changed".
Your findings: `python3 verify.py --for <your-file>.md` (script) and REVIEW-claims-*.md lines naming your file.
Edit the file IN PLACE. Return ONLY: `fixed NN-slug.md — <n> findings applied, <m> skipped (why)`.

## Part 5 (chapters 13-16)
- Findings are in REVIEW-claims-13-14.md and REVIEW-claims-15-16.md.
- The trial build (101 pages) found three text-only pages: the end of 13-vs.md (its last paragraph spilled onto a
  page alone: trim 13.3-13.5 repetition the review lists so it ends on the 153 image's page), 14.2 in 14-friction.md
  (use the new capture `images/170-vs-lesson.png` = `rg -A2 'lesson:' captures/154-vs-friction.txt`, under that
  command in a ```bash block, in place of the plain lesson block), and the end of 16-status.md (its closing
  paragraphs sit alone: shorten them so they fit under the last image, or move 169-git-log3 below them).
- The z.ai 15m lane was still running at capture time: never write that the whole year was compared at 15m.
