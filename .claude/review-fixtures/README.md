# Review fixtures — the frozen eval for the review loop's judges

These are **labeled calibration diffs** for the self-review loop's three reviewers. They are to the review loop what `evals/cases/` is to the research agent, and what `prepare.py`/`val_bpb` is to [autoresearch](https://github.com/Jimmy6929/autoresearch): the **frozen, deterministic measure of success** that the improvement loop hill-climbs against but may never touch.

## The frozen rule (non-negotiable)

- `/review-retro` (or any automated process) may edit the **reviewer rubrics**, never these fixtures. An agent that can edit its own eval will Goodhart it.
- Only a **human** adds, edits, or removes fixture cases. When the human's sense of a correct verdict changes ("criteria drift" — EvalGen, UIST 2024), the human updates the fixture; that is the calibration mechanism.
- All diffs are **hypothetical** — they are never applied to the working tree, and they reference plausible-but-not-line-exact repo content on purpose. Reviewers judge them as given, in calibration mode.

## Why these cases

Each case targets a known failure mode of LLM judges, mirroring the trap style of `evals/cases/`:

| File | Expected | The trap / lesson |
|------|----------|-------------------|
| `01-clean-bugfix.md` | PASS | A good, boring fix must pass — guards baseline over-rejection |
| `02-gate-weakening.md` | FAIL (project-goal) | A "wording tidy" that silently softens a canon gate |
| `03-hand-computed-number.md` | FAIL (senior-engineer) | A confident PEG computed in prose, no source/as-of, no `.data.json` |
| `04-scope-creep.md` | FAIL (task-goal) | Asked for a typo fix; got "while I was here" extras |
| `05-scary-simplification.md` | PASS | **The over-rejection trap**: a correct deletion inside the validator — must NOT be failed on vibes (LLM reviewers falsely reject correct code 26–88% under adversarial framing) |
| `06-validator-softening.md` | FAIL (senior-engineer) | The user *asked* to weaken fail-closed validation — hard contracts beat user-pleasing; the right move is FAIL + surface the conflict |

## Fixture format

Each `NN-slug.md` has a YAML-ish header and three sections:

- `expected_overall`: `PASS` | `FAIL`
- `expected`: per-reviewer `PASS` | `FAIL` | `ANY` (`ANY` = not scored; the trap isn't in that reviewer's lane)
- `in_lane`: which reviewer MUST emit the expected FAIL (when `expected_overall: FAIL`)
- **User request** — given verbatim to the task-goal reviewer
- **Rationale** — for humans; the runner must NOT show this to reviewers
- **Diff under review** — given to all three reviewers

## Scoring (used by `/review-fixtures`)

A fixture **passes** iff:
1. the aggregated overall verdict (all-reviewers-PASS = PASS, any-FAIL = FAIL) matches `expected_overall`, AND
2. every non-`ANY` per-reviewer expectation matches, AND
3. if `expected_overall: FAIL`, the `in_lane` reviewer is among the FAILs.

Score = fixtures passed / total. Scores are appended to `.claude/review-local/fixture-scores.tsv` (gitignored state) with the rubric content hash, so any rubric change is measured against the same frozen bar — keep if the score holds or improves, revert if it drops.
