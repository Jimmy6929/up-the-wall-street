# Research lessons — append-only

One dated line per surprise from a `/research` or `/recheck` run: data quirks,
near-misses on a gate, sources that disagreed. The point is transcript-review
discipline for the *research* runs, the way `.claude/review-local/lessons.md`
does it for the review loop. Append only when something genuinely surprised
you — this file is for signal, not ceremony.

Format: `- YYYY-MM-DD · TICKER · the lesson in one line`

- 2026-06-10 · HRB · seasonal filers can have ONLY the big quarter as standalone quarterly XBRL facts; a naive 4-quarter TTM sums the same quarter from 4 years (now guarded in universe_screen.py, but watch for it in hand-pasted data too)
- 2026-06-10 · CASH · fetch_edgar.py annual_series mis-framed a Sep-30-FYE filer: quarterly EPS came back as "annual", fabricating the scan's 35.6% CAGR (real restated CAGR 15.8%). Engine bug now logged; until fixed, hand-check EPS series for any non-Dec FYE company
- 2026-06-10 · FI · the sec-edgar MCP ticker map predates the FISV→FI rename (lookup by CIK 798354 works); its insider summary also returns filing counts but empty insider name lists - hand-parsed Form 4 XMLs remain the better source
- 2026-06-10 · PLMR · an insurer's "PEG 0.79" can be entirely cycle: zero-hurricane-landfall 2025 + hard market made peak earnings look like secular growth; check what the CORE line grew (3%) before trusting a blended CAGR
