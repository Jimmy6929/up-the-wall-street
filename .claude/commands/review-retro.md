---
description: The review loop's self-improvement pass. Mines escalations, lessons.md, and review-log.tsv for recurring failure patterns, proposes at most 2 minimal delta edits to the reviewer rubrics, then validates them against the frozen fixtures with autoresearch-style keep-or-revert (commit → score → keep if score holds, git reset if it drops). Never edits the fixtures. Use periodically, or after an escalation or a human-overridden FAIL.
---

# /review-retro — consolidate experience into the rubrics, keep-or-revert

You are the **retro curator** for this project's review loop. Your job is the missing half of self-improvement: the loop *logs* its failures; you turn them into **small, validated rubric changes**. The protocol is autoresearch's experiment loop pointed at `.claude/agents/reviewer-*.md` instead of `train.py`: the frozen fixtures are the metric, git is the keep-or-revert mechanism.

## Hard rules (read first)

1. **Never edit `.claude/review-fixtures/`.** It is the frozen eval (`prepare.py` rule). If the evidence suggests a fixture is mislabeled, report that to the human — do not touch it.
2. **Delta edits only, never wholesale rewrites.** Add a bullet, tighten one sentence, or delete a rule. Wholesale rewrites cause context collapse (ACE: one full rewrite compressed an 18k-token playbook to 122 tokens). At most **2 deltas per retro**.
3. **Simplicity criterion** (autoresearch): a rule *deletion* that holds the fixture score is the best outcome; an *addition* must name the concrete incident(s) motivating it. When in doubt, prefer the smaller rubric.
4. **One retro = one commit**, kept or reverted by the score. No unvalidated rubric edits, ever.

## Step 0 — Preconditions

```bash
ROOT="$(git rev-parse --show-toplevel)"
git -C "$ROOT" status --porcelain
```
If the working tree is **not clean**, stop: `⚠ /review-retro: working tree not clean — commit or stash first (the keep-or-revert protocol needs a clean tree).`

## Step 1 — Establish the baseline

Read the latest row of `$ROOT/.claude/review-local/fixture-scores.tsv`.
- If the file is missing or empty, or the latest `rubric_sha` doesn't match the current rubric hash (`cat "$ROOT"/.claude/agents/reviewer-*.md | git hash-object --stdin | cut -c1-7`): run the **/review-fixtures** protocol first to establish the baseline (autoresearch: "your first run is always the baseline"), then continue.
- Baseline = that score.

## Step 2 — Reflect: mine the experience

Read, in this order:
1. `$ROOT/.claude/review-local/escalations/*.md` — what the reviewers could not resolve, and what the human said afterwards (check `git log` around each escalation for how it was actually settled).
2. `$ROOT/.claude/review-local/lessons.md` — including outcomes of past retros.
3. `$ROOT/.claude/review-local/review-log.tsv` — the ledger. Look **both directions**:
   - **Misses**: FAILs/escalations sharing a root cause the rubrics don't name.
   - **False rejections**: FAILs the human overrode or that attempt-2 "fixed" by changing nothing substantive; reviewers repeatedly FAILing on the same vibes-y ground. ReasoningBank: failures AND successes are training data — over-strictness is as real a bug as under-strictness.

Distill at most 2 findings, each in ACE-style itemized form: *pattern → which reviewer's lane → evidence (incident refs) → proposed delta (add / tighten / delete) → expected effect on fixtures*.

If there are **no findings with at least one concrete incident behind them**, stop here and print `✓ /review-retro: nothing to consolidate (no recurring pattern with evidence).` — an empty retro is a valid retro; inventing rules causes bloat (rules without incidents are how 2,000-line CLAUDE.md files die).

## Step 3 — Curate: apply the deltas

Edit the target `.claude/agents/reviewer-*.md` file(s) with the minimal deltas. Each added/changed line should be traceable to its incident (keep the rubric prose clean; put the traceability in the commit message).

Commit:
```bash
git -C "$ROOT" add .claude/agents/ && git -C "$ROOT" commit -m "review-retro: <one-line delta summary>

Motivating incidents: <escalation filenames / ledger dates>"
```

## Step 4 — Validate against the frozen eval

Run the **/review-fixtures** protocol (it appends its own score row with note `post-retro <delta summary>`).

## Step 5 — Keep or revert

- **Score ≥ baseline** → **keep**. The branch advances.
- **Score < baseline** → **revert**: `git -C "$ROOT" reset --hard HEAD~1` (safe: the tree was clean and the only commit is this retro's), and note the failed delta so the next retro doesn't re-try it verbatim.

## Step 6 — Log the outcome

Append to `$ROOT/.claude/review-local/lessons.md`:
```
- <YYYY-MM-DD> · retro · <kept|reverted> · <delta summary> · fixtures <N>/<M> (baseline <B>/<M>)
```

Print:
```
✓ /review-retro: <KEPT|REVERTED> — <delta summary>
  fixtures: <N>/<M> vs baseline <B>/<M> · rubric <sha>
  findings not acted on (if any): <one line each>
```

## Cadence & hygiene

- Run after every escalation, after any human-overridden FAIL, or every ~10 ledger rows — whichever comes first. More often is churn; the signal is incidents, not the calendar.
- **Drift check (monthly):** even with no incidents and no rubric edits, re-run **/review-fixtures** if the latest `fixture-scores.tsv` row is older than ~30 days. Judge behavior drifts with model/config changes (e.g., a `judgeModel` switch) — the calibration set only protects you if it's actually re-scored. A monthly re-score with zero deltas is cheap insurance, and a score drop with *unchanged* rubrics is itself an incident to mine.
- **Rule lifecycle**: while reflecting, list rules added by *past* retros that no subsequent review has cited (search the ledger summaries and recent review output). A rule that never fires across two consecutive retros is a deletion candidate — propose the deletion as one of your 2 deltas (per-rule hit-rate pruning, ACE-style).
- If the same finding gets reverted twice, stop proposing rubric deltas for it and escalate to the human: the gap is probably in the **fixtures** (a case the frozen eval doesn't cover yet) — only the human may add one.
