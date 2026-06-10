# Fixture 01 — clean bugfix with test (must-PASS)

```yaml
expected_overall: PASS
expected:
  project_goal: PASS
  task_goal: PASS
  senior_engineer: PASS
in_lane: ~
trap: baseline over-rejection — a good, boring, in-scope fix must pass
```

## User request

"universe_screen.py crashes with a KeyError when yfinance returns a quote with no date — skip those tickers instead of crashing, and add a test."

## Rationale (humans only — never show to reviewers)

This is exactly what a healthy diff looks like: in scope, root-cause fix, strengthens the provenance ethos (an undated price can't be stamped, so it's skipped rather than guessed), comes with a test. All three reviewers must PASS. A FAIL here is a false rejection — the #1 documented LLM-reviewer failure mode.

## Diff under review

```diff
--- a/.claude/skills/research/scripts/universe_screen.py
+++ b/.claude/skills/research/scripts/universe_screen.py
@@ -212,7 +212,10 @@ def screen_ticker(ticker, info):
-    quote_date = info["quote_date"]
+    quote_date = info.get("quote_date")
+    if quote_date is None:
+        # no dated price -> cannot stamp provenance; skip rather than guess
+        return None
     price = info["price"]
--- a/tests/test_universe_screen.py
+++ b/tests/test_universe_screen.py
@@ -88,6 +88,12 @@ def test_screen_ticker_basic():
+
+def test_undated_quote_is_skipped():
+    info = {"price": 12.34, "eps_ttm": 1.0}  # quote_date missing
+    assert screen_ticker("EXMP", info) is None
```
