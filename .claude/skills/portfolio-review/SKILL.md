---
name: portfolio-review
description: Reviews the whole recommended portfolio for category balance, followability, watering-the-weeds (winners trimmed too early / losers held), concentration, and stale stories. Use when the user asks to review, rebalance, or sanity-check their portfolio or positions as a whole.
---

# Portfolio Review

Look at the positions as a set, not one at a time. Reference: [playbook/07-portfolio.md](../../../playbook/07-portfolio.md). The core truths: you don't need a high hit-rate (a few big winners carry it); own only what you can follow; balance categories; **let winners run**.

## Steps
1. **Load** `portfolio.md` (and `watchlist.md`). For each position note its category, thesis, last-reviewed date, and its preset sell trigger.
2. **Category balance.** Build the target-vs-actual table. Flag imbalance: all ballast (stalwarts/slow growers → no upside) or all fast growers/turnarounds (no downside protection). A healthy mix has both.
3. **Followability.** Count positions vs. how many stories can realistically be rechecked each quarter. If there are more positions than can be followed, recommend consolidating toward the best-understood names (over-diversification dilutes attention, ch. 16).
4. **Watering the weeds.** Flag any **winner being trimmed while its story is still strong** (don't cap upside) and any **loser held with a broken story** (cut it). This is the cardinal portfolio error.
5. **Concentration & correlation.** Too much in one category, industry, or single-customer-dependent name?
6. **Stale stories.** Flag holdings not rechecked recently; recommend a `/recheck` for each.
7. **Output:** the balance table with the gap called out, a followability verdict, and a short list of specific, fundamentals-based actions (consolidate / add to an intact winner / cut a broken loser / let a Watchlist name wait for fear / recheck the stale ones). No market-timing calls.
