---
description: Run this project's LOCAL self-review loop (forked from the global one) on the current uncommitted diff — 3 adversarial reviewers + this project's hard signals (lint/test/typecheck). Aggregates verdicts, manages the retry counter, and escalates to the user on the 2nd consecutive FAIL. Reads config from .claude/review-local.json. Stack-agnostic.
---

# /review-local — Self-Review Loop Coordinator (project-local fork)

You are the **review coordinator** for this project's local self-review loop. This is a project-local fork of the global loop, fully isolated from it. This is the manual entry point; this project's local Stop hook invokes the same flow when you try to finish a turn with reviewable changes.

Everything project-specific comes from `.claude/review-local.json`. Execute the steps below in order.

---

## Step 0 — Load config

```bash
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; echo "ROOT=$ROOT"
cat "$ROOT/.claude/review-local.json" 2>/dev/null || echo "NO_CONFIG"
```

- If there is **no git repo** or **no `.claude/review-local.json`**: print `✓ /review-local: this project has no local review config. Create .claude/review-local.json with "enabled": true to turn the loop on.` and **stop**.
- If `"enabled"` is `false`: print `✓ /review-local: review loop is disabled for this project (enabled=false).` and **stop**.

Read these fields (with defaults):
- `identity` — passed to the project-goal reviewer (default: `"see CLAUDE.md"`).
- `codePaths` — globs that count as code (default: `["**/*"]`).
- `hardSignals` — either `{"autodetect": true}` or an object of named shell commands (default: `{"autodetect": true}`).
- `judgeModel` — model for the reviewer subagents (default: `"inherit"` = same model as you, the coder).
- `maxAttempts` — consecutive FAILs before escalation (default: `2`).

---

## Step 1 — Detect the diff

```bash
git -C "$ROOT" status --porcelain && echo "---" && git -C "$ROOT" diff HEAD --stat
```

Filter the changed files against `codePaths`. If **no changed file matches codePaths** (only docs, only config outside codePaths, or no diff): print `✓ /review-local: nothing to review (no code changes under codePaths).` and **stop**. Do NOT invoke reviewers or hard signals — running the loop on trivial/no changes is wasteful and can degrade good work.

Otherwise continue.

---

## Step 1.5 — Read the lessons back

```bash
tail -30 "$ROOT/.claude/review-local/lessons.md" 2>/dev/null || echo "NO_LESSONS"
```

Pick the **up to 3 entries most relevant to this diff** (same files, same kind of change, same failure mode). Memory only helps if it's read back into the attempt (Reflexion): include the selected entries verbatim in each reviewer prompt in Step 3 as `Relevant lessons from past reviews: <entries>`, and keep them in mind yourself when acting on feedback. If none are relevant, pass none — injecting irrelevant lessons measurably hurts (retrieval ablations favor 1 relevant over many).

---

## Step 2 — Resolve the hard signals

Hard signals are deterministic, **non-overridable** ground-truth checks. They are the part of this loop immune to same-model sycophancy, so treat them as authoritative.

**If `hardSignals.autodetect` is true (or hardSignals is absent):** detect the stack from files present at `$ROOT` and build the command list:

| Detected file | lint | typecheck | test |
|---|---|---|---|
| `package.json` | `npx eslint .` *(only if an eslint config exists)* | `npx tsc --noEmit` *(only if `tsconfig.json` exists)* | the `test` script in package.json, if present (`npm test --silent`) |
| `pyproject.toml` / `ruff.toml` / `setup.cfg` | `ruff check .` *(if ruff available)* | — | `pytest -q` |
| `Cargo.toml` | `cargo clippy --quiet` | (clippy covers it) | `cargo test --quiet` |
| `go.mod` | `go vet ./...` | (vet covers it) | `go test ./...` |

Only include a signal if its tool/config is actually present — never invent one. If nothing is detected, run **zero** hard signals (reviewers still run) and note `hard signals: none detected` in the output.

**If `hardSignals` is an explicit object** (e.g. `{"lint": "ruff check app", "test": "pytest tests -x -q"}`): run exactly those commands. Each command's exit code is its pass/fail (0 = pass).

**Scope tests where cheap.** Prefer scoping tests to files touching the changed source paths when the test runner supports it; otherwise run the project's standard fast test command. Full coverage is the job of CI, not this loop.

---

## Step 3 — Fan out: 3 reviewers + hard signals IN PARALLEL

In a **single message with multiple tool calls**, do all of these concurrently:

1. `Agent` `subagent_type: "reviewer-project-goal"` — pass `model: <judgeModel>` **only if judgeModel is not `"inherit"`/absent**. Prompt: *"Review the current uncommitted diff against your role. The project's identity (from .claude/review-local.json) is: <paste the `identity` field verbatim>. Establish project identity per your instructions, read the diff (git diff HEAD), and output your verdict in the required format."*

2. `Agent` `subagent_type: "reviewer-task-goal"` — same model rule. Prompt: *"Review the current uncommitted diff against your role. The user's most recent request is: <one-sentence summary of what the user asked for>. Judge whether the diff does that — no more, no less. Read the diff (git diff HEAD) and recent commits. Output your verdict in the required format."*

3. `Agent` `subagent_type: "reviewer-senior-engineer"` — same model rule. Prompt: *"Review the current uncommitted diff against your role. Read CLAUDE.md if present and the diff (git diff HEAD). Apply the senior-staff-engineer bar. Output your verdict in the required format."*

4. One or more `Bash` calls running the hard-signal commands resolved in Step 2. Capture each command's exit code (append `; echo "---<NAME> EXIT $?---"`).

Append the Step 1.5 lessons (if any) to each reviewer prompt.

**All calls go in a single message** so they run in parallel — keep review latency low.

> Note on judgeModel: the reviewer agents default to `model: inherit` (same model as you). To use a different judge model for this project, set `judgeModel` in .claude/review-local.json to `opus`, `sonnet`, or `haiku`, and pass it as the `model` option on each Agent call. The research basis: same-model review carries a self-preference bias; a different family mitigates it. The adversarial "default-to-FAIL" prompts + hard signals are the in-loop mitigations when the judge shares the coder's model.

---

## Step 4 — Aggregate the verdict

- **Overall PASS** = all 3 reviewers returned `VERDICT: PASS` **AND** every hard signal exited 0 (or was skipped/not-detected).
- **Overall FAIL** = any reviewer FAIL **OR** any hard signal non-zero exit.

Hard signals are **non-overridable**: any hard FAIL forces overall FAIL even if all 3 reviewers PASS. This guards against same-model sycophancy.

Reviewers may also emit **`NOTES (non-blocking)`** — concerns that didn't meet their evidence bar. Notes **never** affect the verdict. Collect them, count them, and include them in the final report so the human sees them.

---

## Step 5 — Update the attempt counter

State lives under `$ROOT/.claude/review-local/`. Read `$ROOT/.claude/review-local/attempts.json`:
```json
{"task_id": "<sha256 of user's most recent request, first 8 chars>", "attempts": N, "updated_at": "<ISO8601>"}
```
Compute `task_id` from the user's most recent request (`printf '%s' "<request>" | shasum -a 256 | cut -c1-8`).

- If file missing → treat `attempts` as 0.
- If stored `task_id` matches current → use its `attempts`.
- If it doesn't match → new task, reset `attempts` to 0.

On **PASS**: delete `attempts.json` (counter cleared).
On **FAIL**: increment and write back. If `attempts >= maxAttempts`, go to Step 7 (escalation).

---

## Step 6 — Write the result file

Create `$ROOT/.claude/review-local/` if needed and write `$ROOT/.claude/review-local/last-review.json`:
```json
{
  "verdict": "PASS" | "FAIL",
  "attempt": N,
  "timestamp": "<ISO8601 UTC, from: date -u +%Y-%m-%dT%H:%M:%SZ>",
  "diff_sha": "<run: $ROOT/.claude/hooks/review-sha.sh \"$ROOT\" — MUST use this exact helper so the Stop hook's PASS-cache matches>",
  "task_id": "<same as counter>",
  "reviewers": { "project_goal": "PASS|FAIL", "task_goal": "PASS|FAIL", "senior_engineer": "PASS|FAIL" },
  "hard_signals": { "<name>": "pass|fail|skipped", ... }
}
```
The Stop hook reads `diff_sha` + `verdict` to decide whether a prior PASS still covers the current diff.

Then append one row to the **ledger** `$ROOT/.claude/review-local/review-log.tsv` (tab-separated; create with this header row if the file is missing):

```
timestamp	task_id	attempt	verdict	project_goal	task_goal	senior_engineer	hard_signals	notes	summary
```

- `verdict`: `PASS` | `FAIL` | `ESCALATED`.
- `hard_signals`: comma-joined `name:pass|fail|skipped`, or `none`.
- `notes`: count of non-blocking notes across reviewers.
- `summary`: one short plain phrase for what the diff was.

The ledger is **append-only — never rewrite, sort, or trim it**. `last-review.json` answers "what just happened"; the ledger answers "what keeps happening" — it is the raw data `/review-retro` mines for false-rejection patterns and rule hit-rates.

---

## Step 7 — Output

### If PASS:
```
✓ /review-local: PASS (attempt N)

1. Project Goal: PASS — <one line>
2. Task Goal: PASS — <one line>
3. Senior Engineer: PASS — <one line>
Hard signals: <name ✓ · name ✓ · …  or  none detected>
```

### If FAIL and attempts < maxAttempts:
Print the full structured report:
```
✗ /review-local: FAIL (attempt N of <maxAttempts>)

### 1. Project Goal: PASS | FAIL
<full reasoning>

### 2. Task Goal: PASS | FAIL
<full reasoning>

### 3. Senior Engineer: PASS | FAIL
<full reasoning>

### Hard signals
- <name>: pass | fail (<head of failure output if any>)

### Required changes
- [ ] <every required-change line from every reviewer + every failing hard signal, deduplicated>

I will now address these and re-run review.
```
Then **act on the required changes** — fix each one — and automatically re-invoke `/review-local`. Do NOT report "done" to the user until PASS or escalation.

**A retry must be a fix, not a re-roll.** Before re-invoking, you must be able to map each required change to a specific edit you made addressing it. Self-correction research shows untargeted retries saturate immediately (deep errors don't yield to a re-spin). If you cannot map an edit to every finding — because a finding is wrong, ambiguous, or needs a design decision — the right move is to say so and let the loop escalate, not to shuffle code.

### If FAIL and attempts >= maxAttempts:
Go to Step 7-escalation below.

---

## Step 7-escalation — only on the maxAttempts-th consecutive FAIL

1. `TS=$(date -u +%Y-%m-%dT%H-%M-%SZ)`; compute a kebab-case slug (≤40 chars) from the user's request.
2. Write `$ROOT/.claude/review-local/escalations/<TS>-<slug>.md`:
```markdown
# Escalation: <slug>

**Timestamp**: <ISO8601 UTC>
**Task ID**: <task_id>
**Branch**: <current branch>

## Original user request
<verbatim or one-paragraph summary>

## Diff under review
```diff
<git diff HEAD; truncate to 200 lines if longer>
```

## Per-attempt verdicts
<full structured report from each attempt, all 3 reviewers + hard signals>

## What changed between attempts
<what the coder tried to fix between attempts>

## Human, please clarify
<one short paragraph: the specific ambiguity, missing context, or design decision the reviewers cannot resolve without your input.>
```
3. Append one line to `$ROOT/.claude/review-local/lessons.md`:
```
- <YYYY-MM-DD> · <slug> · <maxAttempts>x review fail · see .claude/review-local/escalations/<filename>
```
   Also append a ledger row to `review-log.tsv` with verdict `ESCALATED` (same columns as Step 6).
4. Print:
```
⚠ /review-local: ESCALATED after <maxAttempts> failed attempts.

I tried <maxAttempts> times and could not satisfy the reviewers. Full report:
  .claude/review-local/escalations/<TS>-<slug>.md

Blocker:
<3-sentence summary>

I am stopping here. Please review and clarify.
```
5. **Stop.** Do not retry again. Do not silently continue. (The Stop hook sees `attempts >= maxAttempts` and will let you finish so the user sees this report.)

---

## Notes

- Reviewer rubrics are the **project-local copies** at `.claude/agents/reviewer-*.md` — these override the global ones for this project only. Edit them here freely to tune the loop; the global copies stay untouched.
- Reviewers have **no Write/Edit access** — they only judge. You (the coder) act on their feedback.
- Hard signals are **non-overridable ground truth**. Any hard FAIL forces overall FAIL.
- `.claude/review-local/` (state) is gitignored. The config `.claude/review-local.json` and these `.claude/` files are tracked so the fork travels with the repo.
- This is a fork: the global `/review` command, global reviewer agents, and global Stop hook are all separate and unaffected by edits here.
- **The loop learns, on a frozen eval.** `.claude/review-fixtures/` holds labeled calibration diffs (the loop's `val_bpb`) — run `/review-fixtures` to score the reviewers against them; run `/review-retro` to consolidate escalations + the ledger into small rubric deltas, validated against the fixtures with keep-or-revert. The fixtures are **read-only to the improvement loop**: `/review-retro` may edit rubrics, never fixtures. Only a human adds/edits fixture cases.
