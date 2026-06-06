---
name: research
description: Researches a US-listed stock with Peter Lynch's "One Up on Wall Street" method — classify into one of six categories, screen for green/red flags, compute valuation (PEG) by script, tell the two-minute story, stress-test with an independent skeptic, and issue a Buy candidate / Watchlist / Pass verdict as a sourced markdown note. Use when the user asks to research, analyze, value, or get a verdict on a ticker or company.
argument-hint: <TICKER>
---

# Lynch Research

Run the full Lynch pipeline on **$1** (the ticker/company the user named) and write a sourced research note. You are a research assistant, not a forecaster or trader (see `CLAUDE.md` and `playbook/00-mindset-gates.md`).

> [!important] Two hard rules
> 1. **Never compute valuation in your head.** Delegate the numbers to the `numbers-analyst` subagent, which runs the scripts. Read its output; do not invent or "remember" figures.
> 2. **Every number in the note carries a source + as-of date.** If a figure can't be sourced, say so — don't guess.

## Checklist — copy this into your reply and check off each step

```
Lynch research: $1
- [ ] 0. Gate — honor playbook/00; if this is market timing, decline + redirect
- [ ] 1. Lead — where did the idea come from? (a lead is not a buy signal)
- [ ] 2. Classify — playbook/01 → category + expectation
- [ ] 3. Screen — playbook/02 → green flags, red flags, excitement check
- [ ] 4. Numbers — delegate to numbers-analyst → validated, script-computed metrics
- [ ] 5. Story — playbook/04 → two-minute drill (what / why it grows / what breaks it)
- [ ] 6. Bear case — delegate to skeptic
- [ ] 7. Verdict — playbook/05 → Buy candidate / Watchlist / Pass, fundamentals-justified
- [ ] 8. Write research/<TICKER>.md + save <TICKER>.data.json + update watchlist.md
```

## The steps

**0. Gate.** Re-read `playbook/00-mindset-gates.md`. If the user is really asking you to time the market or predict the economy, decline and redirect to a company. Otherwise proceed.

**1. Lead.** Note in one line where this idea came from and remind that a lead is only a reason to investigate (`playbook/01`…`05` is the investigation).

**2. Classify.** Follow [playbook/01-classify.md](../../../playbook/01-classify.md). Decide the category (slow grower, stalwart, fast grower, cyclical, asset play, turnaround — or "avoid: hype over fundamentals") and state the expectation that category sets. Check the effect on the *whole* company and remember big companies make small moves. **The category drives every later step.**

**3. Screen.** Follow [playbook/02-screen.md](../../../playbook/02-screen.md). List green flags and red flags. Run the excitement check — if the case leans on how thrilling the story is, slow down. Any dominant red flag (hottest-in-hottest, "the next X", whisper/no-earnings, heavy insider selling + crowded ownership) points to **Pass/Avoid** regardless of the numbers.

**4. Numbers — delegate.** Use the **`numbers-analyst`** subagent. Give it the ticker `$1` and the category. It will fetch data (SEC EDGAR → web → ask you), validate provenance, run `compute_valuation.py`, and return the metrics JSON (P/E, historical + forward growth, PEG, dividend-adjusted PEG, net cash, flags). Save its data as `research/<TICKER>.data.json`. If it reports the data can't be validated (e.g., no price), surface that and get the missing figure before continuing — do not fabricate it. Honor its `flags` (especially `cyclical_caveat`).

**5. Story.** Follow [playbook/04-story.md](../../../playbook/04-story.md). Write the category-specific two-minute drill: what it is, why it grows, what would break it. If you can't tell it plainly, the research is incomplete.

**6. Bear case — delegate.** Use the **`skeptic`** subagent. Give it the draft thesis, the category, and the numbers. It returns the strongest refutation and the red flags it found. Include this verbatim-in-spirit as the note's bear case.

**7. Verdict.** Follow [playbook/05-checklist.md](../../../playbook/05-checklist.md). Run the universal + category-specific checklist and map it to **Buy candidate / Watchlist / Pass-or-Avoid**, justified only by fundamentals. Apply the hard stops (cyclical at peak → not a buy on a low P/E; whisper stock → Pass). Set sell triggers in advance.

**8. Write the note.** Create `research/<TICKER>.md` from [templates/research-note.md](../../../templates/research-note.md), filling every section and citing a source + as-of date for each figure. Keep the `research/<TICKER>.data.json` beside it. Update `watchlist.md` (and `portfolio.md` only if the user is actually adding a position). Then give the user a short summary: category, verdict, the one-line story, the key number (PEG or the cyclical caveat), and the main bear-case point.

## Done means
Correct category · script-computed sourced numbers · a plain-language story · an independent bear case · the category-specific checklist · a fundamentals-justified verdict. (These are what `evals/` checks — if unsure, run a relevant case.)
