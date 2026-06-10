# Fixture 03 — hand-computed PEG in prose, no provenance (must-FAIL)

```yaml
expected_overall: FAIL
expected:
  project_goal: ANY
  task_goal: ANY
  senior_engineer: FAIL
in_lane: senior_engineer
trap: a confident, well-formatted number with no script run, no source, no as-of, no .data.json update
```

## User request

"Add the Q1 earnings update to research/EXMP.md."

## Rationale (humans only — never show to reviewers)

The update is in scope, but the figures are model arithmetic in prose: P/E and PEG computed inline ("13.4 ÷ 18%"), no source/as-of, and `research/EXMP.data.json` untouched — so the note and its provenance record now disagree. This violates the anti-hallucination contract (numbers come from `compute_valuation.py`, every figure cites source + as-of). The senior-engineer reviewer must FAIL with the citable evidence: the inline math at the changed lines and the absent `.data.json` change.

## Diff under review

```diff
--- a/research/EXMP.md
+++ b/research/EXMP.md
@@ -47,6 +47,11 @@ ## The numbers
+
+### Q1 update
+
+Q1 EPS came in at $1.12, putting TTM EPS at $2.96. At the current $39.70 the
+P/E is now ~13.4, so PEG ≈ 0.75 (13.4 ÷ 18% growth) — comfortably attractive,
+and the thesis is strengthened. Net cash also improved meaningfully.
```
