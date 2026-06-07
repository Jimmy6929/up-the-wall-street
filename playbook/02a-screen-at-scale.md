# 02a — Screening at Scale (the funnel behind `/scan`)

> [!info] Where this fits
> [02-screen.md](02-screen.md) screens names you already have. This file is the **front of the funnel**: how to turn *the whole market* into a short list of candidates worth that screen — without abandoning a single discipline gate. It is the method behind the `scan` skill and `universe_screen.py`.

## A market scan is a screen, not a verdict

You cannot mass-produce verdicts. A Lynch verdict needs per-company homework — a story, an independent bear case, the category checklist (ch.11–15) — that does not survive being applied mechanically to thousands of names. So a market scan produces **leads** (ch.06: *a lead is not a buy signal*), ranked by the numbers, that then go through the normal `/screen` → `/research` pipeline. The scan's job is to make sure a good, boring, ignored company gets *noticed*; it is never the buy decision.

## The funnel (cheapest filter first)

1. **Universe + quality filter** — free, SEC EDGAR `frames` (one call returns one metric for every filer). Keep names with **positive, consistent, multi-year diluted EPS**. Drops ~90%. No price needed: this answers *"is the business any good?"*, not *"is it cheap?"*
2. **Value the survivors** — re-fetch each survivor's exact `companyfacts`, compute **TTM EPS** (sum of 4 quarters; latest-FY fallback, labeled), attach a price, and run the shared valuation math (`compute_valuation.compute()`) for P/E, PEG, net cash. This answers *"is it cheap for its growth?"*
3. **Qualitative screen** — green/red flags + excitement check on the ranked top (parallel subagents).
4. **Full research** — `/research` on the 1–3 a human picks → a real verdict they read.

Each stage is ~10–100× cheaper than the next, so the expensive homework is only ever spent on names that already cleared a free filter.

## Classify before you rank — and the cyclical trap

**Never sort the whole market by lowest PEG.** A low P/E is a *bargain* on a fast grower and a *danger sign* on a cyclical at peak earnings (ch.15). The script therefore classifies first (by historical EPS CAGR — slow `<5%`, stalwart `5–15%`, fast `≥20%`) and ranks **only** clean, positive-earnings, non-cyclical names. Everything else is set aside for **manual review**:

- **possible_cyclical** — any single-year EPS drop > 20% in the window (a zig-zag).
- **unsustainable growth** — CAGR ≥ 50% (rarely real; needs a human).
- **multi-class shares** — per-share math is unreliable until classes are reconciled.
- **negative / pre-revenue** — EPS ≤ 0: no earnings-based valuation (often out of scope entirely).

> [!warning] The honest limit
> EPS alone **cannot** catch a *monotone-up* cyclical sitting at its peak — its 5-year CAGR looks like a beautiful growth record. EDGAR `frames` give no industry-cyclicality, no inventory trend, no capacity utilization. So the script segregates only the *erratic* and *too-fast*; the real cyclical defense is the **qualitative `/screen` and `/research` classification**. The scan must never claim to have ruled cyclicals out.

## What the script may and may not say

✅ The script emits: numbers (P/E on TTM EPS, PEG, dividend-adjusted PEG, net cash), a category **guess**, and which bucket a name fell into and **why** (reasoned drop tallies — no silent exclusion).
❌ The script never emits: a Buy/Watch/Pass, a "top pick", or any judgment that rests on the story, the excitement, or the price action. Those live in the markdown skills, justified by fundamentals only.

## This is a live screen, not a backtester

The universe is only **currently-listed** filers (survivorship bias) using **latest/restated** figures (look-ahead bias). That is fine for *"what should I look at today?"* — you can only buy listed names and you want the freshest fundamentals — but it is **fatal for any performance claim**. Every `scan-results.md` carries this disclaimer, and the tool asserts no track record.

## Data layer & scope

- **Fundamentals:** SEC EDGAR — authoritative, free, no key. `frames` for the cross-sectional filter (a *filter only*; its calendar/fiscal "best-fit" values never appear in output), exact `companyfacts` re-fetched per survivor for the figures that get shown.
- **Universe definition:** "files a 10-K with `us-gaap` diluted EPS." This excludes ETFs/funds, ADRs, and foreign (20-F/IFRS) issuers by construction — consistent with Lynch's US-centric method.
- **Price:** yfinance, batched + cached, **screening-only** — stamped with its real quote date and **never** cited as the price in a `/research` note. Finalists' prices are re-sourced by hand (the existing EDGAR→web→paste path).
- **Rate limits:** EDGAR is ~10 req/s with an IP-ban penalty; `frames` keeps Stage A to a handful of cached calls, and Stage B re-fetch is throttled and resumable via `.edgar_cache`.

## Upgrade path (documented, not built)

If this screen earns its keep and you outgrow EDGAR, a **point-in-time vendor** — [Sharadar](https://www.sharadar.com/) (cheap, retail-quant standard, survivorship-bias-free, fundamentals since 1990) or Compustat PIT (institutional) — solves TTM, point-in-time history, survivorship, and yfinance fragility in one source. The cost is money and the loss of the free/authoritative-EDGAR ethos, so it is a deliberate later choice, not a default.
