# 07 — Designing a Portfolio (ch. 16)

How the recommended positions fit together. Used by `/portfolio-review`.

## Principles
- **You don't need a high hit-rate.** Because winners can rise many-fold while losers fall at most 100%, a few [tenbaggers] carry the whole portfolio. In ~10 names, expect a few big winners, several mediocre, a few losers — and still do well if the winners run.
- **Own only what you can follow.** The real limit is how many companies you can genuinely research and recheck each quarter — not a fixed number. Owning more than you can follow is worse than owning fewer you know cold. Don't diversify for its own sake at the cost of attention.
- **Spread across categories for balanced risk:** slow growers / stalwarts for stability and downside protection; fast growers, turnarounds, asset plays for upside. Each has a different risk profile, so the blend pursues big gains without betting everything on the riskiest type.
- **Let winners run.** The biggest mistake is selling your best companies too early. While the story is intact and growth continues, hold — even add. Don't cap your upside.

## What `/portfolio-review` checks
1. **Category balance** — is it all ballast (no upside) or all fast growers (no protection)? Flag the imbalance vs. the target mix.
2. **Followability** — are there more positions than can be rechecked each quarter? If so, recommend consolidating toward the best-understood names.
3. **Watering the weeds** — are any winners being trimmed while the story is still strong? Are losers being held with broken stories? Flag both.
4. **Concentration & correlation** — too much in one category, industry, or single-customer-dependent name?
5. **Stale stories** — any holding not rechecked recently (see [06 — Monitor](06-monitor-and-sell.md))?

## Output of `/portfolio-review`
- A category-balance table (target vs. actual) with the gap called out.
- A followability verdict (count of positions vs. what can be tracked).
- Specific flags: winners being trimmed too early, losers with broken stories, over-diversification, stale stories.
- Concrete suggestions (consolidate / add to a winner whose story is intact / let a Watchlist name wait for fear).
