# Research lessons — append-only

One dated line per surprise from a `/research` or `/recheck` run: data quirks,
near-misses on a gate, sources that disagreed. The point is transcript-review
discipline for the *research* runs, the way `.claude/review-local/lessons.md`
does it for the review loop. Append only when something genuinely surprised
you — this file is for signal, not ceremony.

Format: `- YYYY-MM-DD · TICKER · the lesson in one line`

- 2026-06-10 · HRB · seasonal filers can have ONLY the big quarter as standalone quarterly XBRL facts; a naive 4-quarter TTM sums the same quarter from 4 years (now guarded in universe_screen.py, but watch for it in hand-pasted data too)
