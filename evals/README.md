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

## How to score (manual rubric)

There is no built-in runner. To score:

1. Run `/research <TICKER>` (or paste the case's `given_facts` and ask the agent to run the method).
2. Read the resulting note against the case's `expected_behavior` list.
3. Each `expected_behavior` item is **pass/fail**. A case passes only if **all** items pass.
4. The three `trap: true` cases are the most important — the agent must not be seduced into a Buy.

## What a passing run proves

- Correct **classification** (the category drives everything downstream).
- The **category-specific** checklist emphasis is applied (esp. the cyclical P/E trap).
- Numbers come from **`compute_valuation.py`**, not model arithmetic, and every figure cites a source/as-of date.
- A **bear case** is always present.
- The verdict is justified by **fundamentals**, never by price action or the excitement of the story.
