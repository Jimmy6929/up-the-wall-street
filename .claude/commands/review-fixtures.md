---
description: Score this project's review-loop judges against the frozen labeled fixture diffs in .claude/review-fixtures/ (the loop's val_bpb). Runs the 3 reviewer agents in CALIBRATION mode on each fixture, compares verdicts to labels, appends the score to fixture-scores.tsv. Use after any rubric edit, or to establish the baseline before /review-retro.
---

# /review-fixtures — calibrate the judges against the frozen eval

You are the **fixture runner**. You score the three reviewer agents against the labeled diffs in `.claude/review-fixtures/` — the review loop's frozen, deterministic measure of judge quality. You change nothing; you only measure.

## Step 0 — Load

```bash
ROOT="$(git rev-parse --show-toplevel)"; ls "$ROOT/.claude/review-fixtures/"
```

Read every `NN-*.md` fixture (skip `README.md`). From each, extract: `expected_overall`, per-reviewer `expected` (`PASS`/`FAIL`/`ANY`), `in_lane`, the **User request**, and the **Diff under review**. The **Rationale section is for humans — never include it in any reviewer prompt.**

Read `judgeModel` from `.claude/review-local.json` (default `"inherit"`).

## Step 1 — Fan out

For **each fixture**, spawn the three reviewers (`reviewer-project-goal`, `reviewer-task-goal`, `reviewer-senior-engineer`) with this prompt shape (pass `model: <judgeModel>` only if not `"inherit"`):

> CALIBRATION. Judge the following diff, provided inline — do NOT run `git diff`; the diff is hypothetical and not applied to the working tree. The user's request was: "<fixture's User request>". Apply your rubric to this diff exactly as given and output your verdict in your required format.
>
> ```diff
> <fixture's diff, verbatim>
> ```

Do NOT include lessons, the fixture's expectations, or its rationale — calibration measures the rubric alone.

Batch the Agent calls into as few messages as possible (label each `fixture:reviewer`, e.g. `03:senior`) so they run concurrently; the harness queues past the concurrency cap.

## Step 2 — Score

Per fixture:
- **overall** = PASS if all 3 reviewers PASS, else FAIL.
- The fixture **passes** iff: overall matches `expected_overall`, AND every non-`ANY` per-reviewer expectation matches, AND (when `expected_overall: FAIL`) the `in_lane` reviewer is among the FAILs.

Score = passed / total.

## Step 3 — Record

Compute the rubric hash (identifies which rubric version was measured):
```bash
cat "$ROOT"/.claude/agents/reviewer-*.md | git hash-object --stdin | cut -c1-7
```
Append one row to `$ROOT/.claude/review-local/fixture-scores.tsv` (tab-separated; create with header if missing — and `mkdir -p` the dir):
```
timestamp	rubric_sha	score	total	failed_fixtures	note
```
- `failed_fixtures`: comma-joined fixture names that failed, or `none`.
- `note`: short context, e.g. `baseline` or `post-retro <delta summary>`.

This file is **append-only**.

## Step 4 — Report

Print a table: fixture · expected · got (per reviewer + overall) · pass/fail, then the score line:

```
/review-fixtures: N/M (rubric <sha>)
```

For each failed fixture, one sentence on *how* it failed — a must-PASS that got FAILed is a **false rejection** (over-strict rubric); a must-FAIL that got PASSed is a **miss** (under-strict rubric). Name which direction dominates, since the fix differs.

## Rules

- Never edit anything under `.claude/review-fixtures/` — it is the frozen eval. If a fixture seems wrong, say so in the report and let the human change it.
- Never count a fixture as passed because the reviewer's *reasoning* was close — only the VERDICT lines score.
