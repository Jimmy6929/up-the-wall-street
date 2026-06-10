# Evals

These cases define what "thinks like Lynch" means. They were written **before** the playbook, so the playbook is built to pass them (per Anthropic's "build evaluations first" guidance).

Each case in `cases/` is a self-contained JSON with **fictional** companies, so it is reproducible without live data and cannot be read as real advice. The `given_facts` block is fed to the agent as if pasted by the user (the manual-data path), so no network is needed to run an eval.

## The cases

| File | Archetype | The trap / lesson |
|------|-----------|-------------------|
| `01-stalwart-clean.json` | Quality stalwart, full price | Right category + a Watch (price-rich), not a reflexive Buy |
| `02-fast-grower.json` | Small fast grower, long runway | PEG < 1 + proven runway → a genuine Buy candidate |
| `03-cyclical-peak-trap.json` | Cyclical at peak earnings | **A low P/E at peak earnings is a danger sign, not a bargain** |
| `04-hot-stock-avoid.json` | Hottest stock in hottest industry | Excitement is a yellow flag; "the next X"; competition kills the margin |
| `05-whisper-stock-avoid.json` | Pre-revenue "miracle" story | No earnings to value; a thrilling story is the bait, not the thesis |
| `06-derivatives-out-of-scope.json` | Option/short request | **Out of scope (ch. 19): decline the derivative, redirect to the underlying — without forecasting the price** |
| `07-turnaround.json` | Recovering near-failure | Balance sheet first: can it survive the debt? Recovery, not a growth multiple |
| `08-asset-play.json` | Hidden land value | Assets need a **catalyst**; P/E is beside the point for this category |
| `09-slow-grower-dividend.json` | Regulated utility | Owned for the dividend; check payout safety; ballast, never a tenbagger |
| `10-recheck-broken-story-sell.json` | Held fast grower, story broken | **Sell on the broken story, by category rules — "down 35%, feels like a bargain" justifies nothing (ch. 18)** |

## How to score

### Automated (the harness)

`evals/run_evals.py` runs each case in a headless Claude Code session and grades it in
two layers — deterministic **code graders** (frontmatter category vs `category_truth`,
verdict vs `grade.verdict_allowed`, every metrics-table number re-checked against
`compute_valuation.py`, bear-case section, the structural sources gate) and an
**LLM judge** (opus, not the coder's model) over the frozen `expected_behavior` items.
Reliability is **pass^k**: a case passes only if all k trials pass.

```
scripts/evals --smoke              # trap cases only, k=1 (routine)
scripts/evals                      # all cases, pass^3 (before trusting changes)
scripts/evals --no-judge           # code graders only (cheap)
scripts/evals --grade-only evals/runs/<ts>   # re-grade, no agent runs
```

Scores append to `evals/scores.tsv` (append-only ledger); per-trial artifacts go to
`evals/runs/<timestamp>/` (gitignored). **Cost note:** every trial is a full headless
`/research` run and draws from the Agent SDK credit on subscription plans.

**Frozen-labels rule (anti-Goodhart):** `expected_behavior` lists are human-written and
only a human may change them — same rule as `.claude/review-fixtures/`. The additive
`grade` blocks (machine-checkable labels) are part of the eval and frozen the same way.

### Manual (fallback, unchanged)

1. Run `/research <TICKER>` (or paste the case's `given_facts` and ask the agent to run the method).
2. Read the resulting note against the case's `expected_behavior` list.
3. Each `expected_behavior` item is **pass/fail**. A case passes only if **all** items pass.
4. The `trap: true` cases are the most important — the agent must not be seduced into a Buy (or, in case 10, out of a Sell).

## What a passing run proves

- Correct **classification** (the category drives everything downstream).
- The **category-specific** checklist emphasis is applied (esp. the cyclical P/E trap).
- Numbers come from **`compute_valuation.py`**, not model arithmetic, and every figure cites a source/as-of date.
- A **bear case** is always present.
- The verdict is justified by **fundamentals**, never by price action or the excitement of the story.
