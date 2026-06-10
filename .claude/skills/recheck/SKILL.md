---
name: recheck
description: Re-tests the story of a stock you already hold or watch, re-running the numbers and the three monitoring questions, and decides Hold / Add / Sell by Lynch's category-specific rules. Use when the user wants to recheck, re-review, or revisit a holding or watchlist name, or asks "should I still hold X?".
argument-hint: <TICKER>
---

# Recheck

Re-examine the story of **$1**. Buying isn't the end of the work; monitoring is. Reference: [playbook/06-monitor-and-sell.md](../../../playbook/06-monitor-and-sell.md). Sell only for fundamental reasons — **never** for price, fear, or boredom.

## Steps
1. **Load the prior thesis.** Read `research/<TICKER>.md` (and `<TICKER>.data.json`) and `watchlist.md`/`portfolio.md`. Note the category and the original story + sell triggers.
2. **Refresh the numbers.** Delegate to the **`numbers-analyst`** subagent to re-fetch and recompute (fresh price, EPS, growth, PEG). Overwrite `<TICKER>.data.json`; keep provenance.
3. **Answer the three questions** (ch. 14):
   - Still **cheap vs. growth**? Has the PEG / P/E-vs-growth stretched?
   - Still **growing from here** — what makes it grow *going forward*, not just what already happened?
   - Any **new obstacles** (competition, debt, saturation, a stalled catalyst)?
4. **Check category-specific signals** (fast grower runway; cyclical cycle position + inventories; turnaround recovery + debt; asset-play catalyst; stalwart multiple).
5. **Decide: Hold / Add / Sell**, with a fundamentals-based, category-specific reason:
   - *Add* when a fast grower is in its proven, not-yet-saturated middle innings, or a Watchlist name has hit your pre-set fear-discount price.
   - *Sell* when the **story has played out or broken** for the category (fast grower's runway gone / P/E ballooned; cyclical near peak; turnaround fully recovered; asset value unlocked).
   - *Hold* when the story is intact — let winners run; do not trim a winner just because it's up (watering the weeds).
6. **Update** `research/<TICKER>.md` (reviewed date + the re-told story), `watchlist.md`, and `portfolio.md`. Summarize the decision and the one reason for it.
7. **Lesson (optional, one line).** If anything in the recheck surprised you — a sell trigger that fired, a number that didn't refresh cleanly, a story drift you nearly rationalized — append one dated line to `research/lessons.md`. Skip silently if nothing did.

> [!warning] Forbidden reasons to sell
> "It dropped" (panic), "it's up" (nerves), "nothing's happened yet" (boredom), "I'll wait till it's back to even" (anchoring). The business is the signal, not the price.
