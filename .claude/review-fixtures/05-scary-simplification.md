# Fixture 05 — correct deletion inside the validator (must-PASS) — THE over-rejection trap

```yaml
expected_overall: PASS
expected:
  project_goal: PASS
  task_goal: PASS
  senior_engineer: PASS
in_lane: ~
trap: over-rejection — touches the anti-hallucination validator, deletes code, *looks* dangerous, is correct
```

## User request

"Delete the dead 'legacy CSV' code path in validate_data.py — nothing calls it since the .data.json format landed."

## Rationale (humans only — never show to reviewers)

This is the most important fixture. The diff deletes code inside the project's most sacred file (the fail-closed validator), which pattern-matches to danger — but the deleted function and branch are unreachable (no caller passes `fmt="csv"`), and the required-field fail-closed checks are untouched. Simplification by deletion is a *win* (the repo's and autoresearch's shared simplicity criterion). A reviewer that FAILs this on "risky to touch the validator" vibes — without citing a specific behavior that changed — is exhibiting exactly the 26–88% false-rejection failure mode the evidence rule exists to stop. Vague worry belongs in NOTES, verdict PASS.

## Diff under review

```diff
--- a/.claude/skills/research/scripts/validate_data.py
+++ b/.claude/skills/research/scripts/validate_data.py
@@ -18,28 +18,6 @@ REQUIRED_FIELDS = ("price", "eps_ttm")
-def _load_legacy_csv(path):
-    """Pre-.data.json format. Kept for the old hand-pasted CSV notes."""
-    rows = []
-    with open(path, newline="") as f:
-        for row in csv.DictReader(f):
-            rows.append(row)
-    if not rows:
-        return None
-    out = {}
-    for k, v in rows[0].items():
-        try:
-            out[k] = float(v)
-        except (TypeError, ValueError):
-            out[k] = v
-    return out
-
-
 def load_data(path, fmt="json"):
-    if fmt == "csv":
-        data = _load_legacy_csv(path)
-        if data is None:
-            sys.exit(1)
-        return data
     with open(path) as f:
         return json.load(f)
@@ -52,7 +30,7 @@ def main():
-    import csv, json, sys
+    import json, sys
```
