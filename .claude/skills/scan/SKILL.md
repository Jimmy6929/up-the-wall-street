---
name: scan
description: Scan the whole US market (or a ticker subset) for Lynch-style candidates. Runs the deterministic universe_screen.py funnel, then fans out the qualitative green/red-flag screen across the top candidates and recommends 1-3 for a full /research. Produces leads, never verdicts. Use when the user wants to discover names across the market rather than research one they already named.
argument-hint: [tickers, or blank for the full universe]
---

# Scan

Find candidates across the market so the user isn't limited to tickers they already thought of. This is a **funnel that ends in leads, not verdicts** — the deterministic script does the numbers and a category *guess*; you and the subagents do the qualitative judgment; a human does the buying. Reference: [playbook/02a-screen-at-scale.md](../../../playbook/02a-screen-at-scale.md), [playbook/02-screen.md](../../../playbook/02-screen.md).

> The script emits numbers + a category guess and **never** a Buy/Watch/Pass. A scan output is a list of *leads* (ch.06: "a lead is not a buy signal"). Real verdicts only come from `/research`.

## Steps

1. **Run the engine** (deterministic, never compute these by hand):
   - Subset: `python3 .claude/skills/research/scripts/universe_screen.py --tickers AAPL,KO,... --write-leads`
   - Full universe: `python3 .claude/skills/research/scripts/universe_screen.py --write-leads` (slower; throttled EDGAR + yfinance).
   - It writes `scan-results.md` (ranked candidates + a **manual-review** section + reasoned drop tallies + the bias disclaimer) and, with `--write-leads`, appends the top-N to `leads.md` as labeled leads.
   - Read `scan-results.md`. Do **not** re-derive or "remember" any number — the script is the source of truth.

2. **Fan out the qualitative screen** over the **ranked** candidates. In a single message, launch parallel subagents (Agent tool), **~5 candidates each**, each applying [playbook/02-screen.md](../../../playbook/02-screen.md) to its batch:
   - Treat the script's category as a **guess** — re-classify (size, maturity, economic sensitivity, hidden assets), since the script can't tell a slow-monotone **cyclical** from a stalwart.
   - Tally green flags (niche, repeat-purchase, boring/ignored, low institutional ownership, insider buying, buybacks, spinoff, tech-user) and red flags (hottest-in-hottest, "the next X", whisper/no-earnings, diworseification, single-customer).
   - **Excitement check** (thrill is a yellow flag) and a lean: `research` / `maybe` / `skip`.
   - Each subagent returns a short table: Ticker | re-classified category | green | red | lean.

3. **Completeness critic.** Launch one more subagent to audit the run:
   - Did a whole **category** silently vanish (e.g. all stalwarts dropped by a frames quirk)? Check the drop tallies in `scan-results.md` by reason.
   - Is any **ranked** name a likely cyclical-at-peak the EPS filter missed (low PEG + capital-intensive/commodity business)? Flag it down to manual.
   - Did any **manual-review** name get set aside for a bad reason and actually deserve a look?

4. **Recommend 1-3 names** to take to a full `/research` — the boring survivors with clean green flags, not the exciting ones. Update `leads.md` Status (`lead → researching`) for those, `lead → passed` for dominant-red-flag names.

## Output of this step
- A consolidated table (ranked candidate | re-classified category | green | red | lean).
- The critic's findings (anything re-routed, any coverage gap).
- The 1-3 names recommended for `/research`, with one line each on *why* (fundamentals, not excitement).

Keep the engine agent-free and the judgment human/LLM. A boring candidate surviving the screen is a good sign; an exciting one is a reason to be more skeptical, not less.
