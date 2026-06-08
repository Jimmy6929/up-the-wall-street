# 00a — Book Map (chapter → workflow traceability)

This is the **living traceability record** between *One Up on Wall Street* and this agent's
workflow. It exists to answer one question on demand — *"is the whole workflow still
following the book?"* — and to make drift **visible** the moment a chapter loses its home.

`tests/test_book_map.py` parses this file: it fails if any chapter (00–20) or concept note
loses its row, if any status is `MISSING`, or if a file referenced here doesn't exist on
disk. So this map is **enforced**, not just asserted.

## The book is not 21 linear steps — it is three modes

A common misread is "every chapter is one step you run per stock." Only the middle third is.
The book is three parts, and the workflow mirrors them:

- **GATE** — *Part I (ch 00–05) + the psychology chapters (18, 20).* Always-on rules, not
  per-stock steps. Honored on **every** request. Home: [`playbook/00-mindset-gates.md`](00-mindset-gates.md).
- **PIPELINE** — *Part II (ch 06–15).* The actual per-stock sequence: lead → classify →
  screen → numbers → story → checklist → verdict. Home: `playbook/01`…`05` + the
  [`research`](../.claude/skills/research/SKILL.md) skill.
- **ONGOING** — *Part III (ch 16–17).* Habits you repeat for as long as you hold: recheck,
  buy on fear, sell only on a broken story, design the portfolio. Home:
  [`playbook/06-monitor-and-sell.md`](06-monitor-and-sell.md), [`playbook/07-portfolio.md`](07-portfolio.md).

Forcing these into one linear list would make the agent *less* faithful (it would turn
always-on gates and lifelong habits into one-time checkboxes), so we keep the three modes
distinct on purpose.

Status legend: **FAITHFUL** = the chapter's think→action step is implemented as Lynch
states it · **PARTIAL** = present but lighter than the book · **MISSING** = no home (the test
fails on this).

## Chapters

| Ch | Think → action | Mode | Home | Status |
|---|---|---|---|---|
| 00 | Amateurs have a real edge; trust what you already know, don't ape Wall Street | GATE | `playbook/00-mindset-gates.md` (g1,3,7); `CLAUDE.md` | FAITHFUL |
| 01 | Stock-picking is a learnable craft built on observing real businesses | GATE | `CLAUDE.md`; `playbook/01-classify.md` | FAITHFUL |
| 02 | Pros are structurally constrained (career risk, rules, herd) → hunt what they *can't* buy | GATE | `playbook/00-mindset-gates.md` (g7); `playbook/02-screen.md` (low-institutional-ownership flag) | FAITHFUL |
| 03 | Investing vs. gambling = homework + a long horizon; risk is ignorance and impatience | GATE | `playbook/00-mindset-gates.md` (g3,6) | FAITHFUL |
| 04 | The mirror test: temperament over IQ — can you hold through a drawdown, with money you won't need | GATE | `playbook/00-mindset-gates.md` (g9, the human's self-check); `.claude/skills/research/SKILL.md` (step 8, surfaced on a Buy) | FAITHFUL |
| 05 | Do not forecast the market or the economy | GATE | `playbook/00-mindset-gates.md` (g1) | FAITHFUL |
| 06 | Leads come from your own life; a lead is not a buy — investigate, and look firsthand | PIPELINE | `.claude/skills/research/SKILL.md` (step 1, firsthand field); `playbook/02a-screen-at-scale.md`; `leads.md` | FAITHFUL |
| 07 | Classify first — the category sets expectations, strategy, and sell rules | PIPELINE | `playbook/01-classify.md` | FAITHFUL |
| 08 | The perfect stock is dull/ignored — 13 green-flag attributes | PIPELINE | `playbook/02-screen.md` | FAITHFUL |
| 09 | Stocks to avoid — hottest-in-hottest, "the next X", whisper, diworseification, single-customer | PIPELINE | `playbook/02-screen.md` | FAITHFUL |
| 10 | Earnings drive the price; the P/E is the price of earnings | PIPELINE | `playbook/03-numbers.md` | FAITHFUL |
| 11 | The two-minute drill — tell the story plainly or you don't own it | PIPELINE | `playbook/04-story.md` | FAITHFUL |
| 12 | Getting the facts — annual report, IR call, kick the tires, your own eyes | PIPELINE | `playbook/03-numbers.md` (Getting the facts); `.claude/skills/research/SKILL.md` (step 1) | FAITHFUL |
| 13 | The famous numbers — PEG, cash vs. debt, dividends, book value, cash flow, inventories | PIPELINE | `playbook/03-numbers.md`; `.claude/skills/research/scripts/compute_valuation.py` | FAITHFUL |
| 14 | Recheck the story on a cadence — still cheap? still growing? new obstacles? | ONGOING | `playbook/06-monitor-and-sell.md`; `.claude/skills/recheck/SKILL.md` | FAITHFUL |
| 15 | The final checklist — category-specific verification → verdict | PIPELINE | `playbook/05-checklist.md` | FAITHFUL |
| 16 | Design a portfolio — a few tenbaggers carry it; own only what you can follow; let winners run | ONGOING | `playbook/07-portfolio.md`; `.claude/skills/portfolio-review/SKILL.md` | FAITHFUL |
| 17 | Best time to buy/sell — buy on fear; sell when the story breaks, by category | ONGOING | `playbook/06-monitor-and-sell.md` | FAITHFUL |
| 18 | The twelve silliest things — price action is not business judgement; don't anchor to cost | GATE | `playbook/00-mindset-gates.md` (g2); `playbook/06-monitor-and-sell.md` (never sell for the wrong reasons) | FAITHFUL |
| 19 | Options, futures, shorts discard the amateur's edge → out of scope | GATE | `playbook/00-mindset-gates.md` (g10, decline + redirect); `CLAUDE.md` (Scope) | FAITHFUL |
| 20 | The crowd is often wrong — think independently, then verify with homework | GATE | `playbook/00-mindset-gates.md` (g7); `.claude/agents/skeptic.md` | FAITHFUL |

## Concept notes

| Concept | Home | Status |
|---|---|---|
| Invest in What You Know | `.claude/skills/research/SKILL.md` (step 1 firsthand); `playbook/02a-screen-at-scale.md` | FAITHFUL |
| The Six Categories of Stocks | `playbook/01-classify.md` | FAITHFUL |
| The Perfect Stock | `playbook/02-screen.md` (13 green flags) | FAITHFUL |
| Stocks to Avoid | `playbook/02-screen.md` (red flags) | FAITHFUL |
| The Two-Minute Drill | `playbook/04-story.md` | FAITHFUL |
| The PEG Ratio | `playbook/03-numbers.md`; `.claude/skills/research/scripts/compute_valuation.py` | FAITHFUL |
| The Final Checklist | `playbook/05-checklist.md` | FAITHFUL |
| The Tenbagger | `playbook/01-classify.md`; `playbook/07-portfolio.md` | FAITHFUL |
| Watering the Weeds | `playbook/06-monitor-and-sell.md`; `playbook/07-portfolio.md` | FAITHFUL |

## Modern application

| Note | Home | Status |
|---|---|---|
| Peter Lynch on AI Stocks (2025) | `CLAUDE.md` (Scope); `playbook/00-mindset-gates.md` (g5 "know what you own") | FAITHFUL |

## How to keep this honest

- Edit a playbook step? Update the matching row here in the same change. The test will fail
  if a chapter's referenced file disappears.
- Add a new step or skill? Add the chapter/concept it serves, or note here why it has no
  book source (an explicit, faithful *addition* — e.g. the deterministic scripts, the skeptic
  subagent — rather than silent drift).
- A row that honestly cannot be implemented yet should read `MISSING` (not be deleted) so the
  gap stays loud.
