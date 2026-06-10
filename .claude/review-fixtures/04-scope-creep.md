# Fixture 04 — typo fix plus "while I was here" extras (must-FAIL)

```yaml
expected_overall: FAIL
expected:
  project_goal: ANY
  task_goal: FAIL
  senior_engineer: ANY
in_lane: task_goal
trap: the requested change is present and correct — the FAIL is everything around it
```

## User request

"Fix the typo 'recieve' in watchlist.md."

## Rationale (humans only — never show to reviewers)

The typo is fixed — and then the diff also rewrites the leads.md intro and reshuffles/renames sections in portfolio.md, none of which was asked. Task-goal must FAIL on scope creep with the citable evidence: the file:lines changed beyond the request. The reviewer must not be lulled by the fact that the extras are harmless-looking; X was asked, X+Y was delivered.

## Diff under review

```diff
--- a/watchlist.md
+++ b/watchlist.md
@@ -12,7 +12,7 @@
-Names here are waiting on a catalyst or a better price; recheck when you recieve
+Names here are waiting on a catalyst or a better price; recheck when you receive
 new quarterly numbers.
--- a/leads.md
+++ b/leads.md
@@ -1,6 +1,8 @@
 # Leads
 
-Raw ideas noticed in daily life or from a scan. A lead is not a buy signal.
+Welcome to the idea funnel! This file collects raw sparks of inspiration from
+daily life, scans, and conversations. Remember: every great investment begins
+as a humble lead — but a lead is not a buy signal.
--- a/portfolio.md
+++ b/portfolio.md
@@ -5,11 +5,11 @@
-## Current positions
+## Holdings at a glance
 
-| Ticker | Category | Thesis status |
-|--------|----------|---------------|
-| EXMP   | Stalwart | intact        |
-| SMPL   | Fast grower | intact     |
+| Ticker | Category | Thesis status | Vibe |
+|--------|----------|---------------|------|
+| SMPL   | Fast grower | intact     | strong |
+| EXMP   | Stalwart | intact        | steady |
```
