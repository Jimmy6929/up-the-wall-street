---
title: CSV — Carriage Services, Inc.
ticker: CSV
company: Carriage Services, Inc.
type: research-note
category: Slow grower (small-cap death-care roll-up; moderate, largely acquisition-driven growth)
verdict: Watchlist
peg: 2.80 (rich on 5% fwd; ~1.9 on bullish 7.4%)
as_of: 2026-06-08
reviewed: 2026-06-08
tags: [research, slow-grower, death-care]
---

# CSV — Carriage Services, Inc.

> [!summary] Verdict: **Watchlist** (re-research 2026-06-08; reaffirms the 2026-06-07 call, now at a richer price)
> A genuinely defensive, non-cyclical death-care niche (Lynch's "something depressing about it" archetype) — but **not a buy at this price**. On today's $45.46 the PEG is **2.80 (rich)** on a conservative ~5% forward estimate (~1.9 even on the bullish 7.4% consensus); the balance sheet is **leveraged ~4.0×** (net debt −$527M ≈ ~$33/share, vs a $45 price), with **$397M of 4.25% notes to refinance in 2029** into a ~6% market; **organic funeral volume is declining** (Q1 2026 comparable contracts −5.8%, adjusted EPS −10.4% YoY); a structural **cremation** shift erodes revenue/margin per case; and a **$100M ATM** arms dilution while buybacks sit dormant. The ~1% dividend doesn't pay you to wait. Good business, wrong price — own only materially cheaper, after it delevers and organic volume re-inflects.

## 1. Lead (ch. 06)
Re-research of a name already on the watchlist (originally surfaced by `/scan`, "Moderate grower" guess, apparent cheap PEG that proved to be an artifact of a one-off-inflated historical CAGR). User re-ran `/research CSV` on 2026-06-08; the price input has risen to **$45.46** from **$37.53** (2026-06-05), which makes the valuation richer (a PEG fact, not a price-action verdict — the gates forbid reasoning from the chart).
**Firsthand observation (ch. 12):** none provided — sourced from the screen + filings. (Deathcare is Lynch's literal "depressing business" archetype; that's a green flag, not a thesis.) **A lead is not a buy signal.**

## 2. Classification (ch. 07)
**Category:** **Slow grower** in a no-growth, recession-resistant industry — the #2 public US death-care company (funeral homes + cemeteries), a small-cap (~$0.7B) that grows via **acquisitions + pricing + pre-need sales** rather than organic volume. Management calls itself "a consolidation company." Demand is **non-cyclical / demographically driven** — explicitly **not** a cyclical, so no peak-P/E cyclical trap applies (`cyclical_caveat` did not fire). It carries small-cap, leveraged-roll-up characteristics, not blue-chip-stalwart stability — so I classify it slow grower rather than stalwart (the prior note's label), though both lenses ask the same governing question: **is the price reasonable for the growth, and can the balance sheet carry the debt?**
**Expectation set:** modest, steady, debt-amplified — *not a tenbagger*. **Effect on whole company:** acquisitions + same-store pricing move total earnings; the secular shift to (cheaper) cremation is the structural drag, and organic case volume is currently shrinking, so reported growth increasingly *depends on continued debt-funded M&A*.

## 3. Screen (ch. 08–09)
- **Green flags:** "something depressing about it" — *funeral services is Lynch's literal example*; **non-cyclical, recession-resistant**; a **niche** with switching costs (families return to known local funeral-home brands); under-followed small-cap, institutional ownership ~73–78% (below the crowded threshold — room to be discovered); **insiders net buying** (~$580k open-market over the past year).
- **Red flags:** **leveraged roll-up** (~4.0× net-debt/EBITDA; net debt ≈ ~$33/share vs a $45 price; $397M notes due 2029); **acquisition-dependent growth** — 2026 guidance even bakes in revenue from *unannounced* deals; **structural cremation headwind** (cheaper disposition → lower revenue + margin per case); **declining organic volume** (−5.8% comparable funeral contracts, Q1 2026); a **$100M ATM** diluting equity while **buybacks are dormant** (the green flag absent, the dilution flag armed); **lumpy, one-off-distorted GAAP earnings**.
- **Excitement check:** **low — which is green** ("boredom is often green"). The thesis correctly rests on defensive earnings, not thrill. The problem is **price + leverage + a secular volume headwind**, not hype.

## 4. The numbers (ch. 10–13) — *computed by `compute_valuation.py`*
| Metric | Value | Source | As of |
|---|---|---|---|
| Price | $45.46 | Investing.com / Yahoo / CNBC intraday (NYSE:CSV) | 2026-06-08 |
| EPS (ttm, FY2025 GAAP) | $3.25 *(adj. ~$3.20; clean TTM-thru-Q1'26 ~$2.77 — see Read)* | SEC EDGAR companyfacts (EPSDiluted, FY2025) | 2025-12-31 |
| P/E | 13.99 *(on GAAP $3.25; ~16.4 on clean TTM $2.77)* | computed | 2026-06-08 |
| EPS history FY21→25 | 1.81 / 2.63 / 2.14 / 2.10 / 3.25 (lumpy) | SEC EDGAR companyfacts | FY21–25 |
| Earnings growth (hist. CAGR) | 15.8% *(inflated by FY25 rebound off a FY24 trough — do not use)* | computed | — |
| Growth estimate (fwd) | ~5% conservative *(co. FY26 adj-EPS guide midpoint ~6%; consensus to ~7.4%)* | company guidance / consensus | 2026-06-08 |
| **PEG (on 5% fwd)** | **2.80 — `peg_rich`** *(~1.9 on 7.4%)* | computed | 2026-06-08 |
| Dividend-adj. PEG (g+y)/PE | 0.43 *(poor on the scale)* | computed | 2026-06-08 |
| Dividend yield | 0.99% ($0.45/yr) | computed | 2026-06-08 |
| **Net cash (cash − debt)** | **−$527.25M (−$33.47/sh)** · ~4.0× net-debt/adj-EBITDA | SEC EDGAR FY2025 10-K | 2025-12-31 |
| Institutional ownership | ~73–78% (not crowded) | MarketBeat / Nasdaq 13F | 2026-06-08 |
| Insider activity / capital allocation | **Net insider buying** (~$580k open-market); **$100M ATM** program (dilution); buybacks dormant | SECForm4 / 10-Q / 424B5 | 2026-06-08 |

**Read:** The decisive, disciplined number is **`peg_rich`**. On today's price and a conservative ~5% forward growth, PEG is **2.80**; even on the bullish ~7.4% consensus it is ~**1.9** — rich on any estimate. PEG uses **forward** growth, *not* the corrupted 15.8% historical CAGR (FY2024 was a trough depressed by severance/strategic-review costs; FY2025 GAAP $3.25 was lifted by divestiture gains, so adjusted FY2025 is ~$3.20). **The verdict is robust to the earnings base:** the prior note's cleaner TTM-through-Q1'26 EPS of ~$2.77 puts P/E at ~16.4 and PEG *higher* still — i.e., using GAAP $3.25 here *understates* the richness. The dividend-adjusted PEG (0.43) is **poor** (the ~1% yield can't rescue it). The dominant balance-sheet fact: **net debt ≈ ~$33 of a $45 share**, ~4.0× leverage near management's ceiling, with **$397M of 4.25% Senior Notes due 2029** facing a refi into a ~5.85% BB high-yield market (≈ +$7–11M annual pre-tax interest, ~$0.35–0.55/share — roughly a year of the entire growth estimate). *(Per the gates: this verdict rests on the rich PEG, the leverage/refi, the declining organic volume, and the cremation headwind — not on the price's recent move.)*

## 5. The two-minute drill (ch. 11)
1. **What it is:** Carriage Services owns and runs funeral homes and cemeteries across the US (the #2 public death-care company), serving families through trusted local funeral-home brands.
2. **Why it grows:** recession-resistant demand + price increases + acquisitions of independent funeral homes + pre-need (prepaid) sales that build a deferred backlog. *Caveat: growth is increasingly acquisition- and price-driven — organic case volume is currently falling (−5.8% Q1 2026).*
3. **What breaks it:** the secular shift to **cheaper cremation** (lower revenue + margin per case) the local-brand niche can't offset; **high leverage** (~4×, 2029 notes to refinance into higher rates); **ATM dilution**; overpaying for acquisitions (diworseification); and simply **paying a rich price** (PEG ~2.8 on 5%, ~1.9 on 7.4%) for a token-dividend, single-digit grower.

**Headline story (watchlist):** *"Defensive death-care roll-up; real niche but fully-priced (PEG ~2.8) and leveraged (~4×) with a 2029 refi and declining organic volume — watch for a much cheaper price."*

## 6. Bear case (the skeptic, ch. 09/20)
1. **The headline P/E rests on overstated earnings, and the most recent quarter is going the wrong way.** GAAP FY2025 $3.25 carries divestiture/special-item gains (adjusted ~$3.20). More telling, **Q1 2026 adjusted EPS fell 10.4%** ($0.86 vs $0.96) and **comparable funeral volume fell 5.8%** (10,663 vs 11,319), on revenue down $0.9M. Reported full-year "growth" is back-half- and acquisition-dependent.
2. **Cremation is a permanent revenue/margin headwind.** US cremation ~63% (2025) heading toward ~82% by 2045; peer SCI's core funeral services performed also fell in 2025. High-fixed-cost businesses with falling volume run operating leverage in reverse — and CSV must keep *buying* revenue just to stand still.
3. **The 2029 refinancing is a near-certain, dated EPS hit.** $397.5M at 4.25% rolling into a ~5.85% BB high-yield market (likely worse for a 4.0× name) ≈ +$7–11M annual interest, ~$0.35–0.55/share — capable of erasing a year-plus of the growth story. The bull case isn't pricing it.
4. **Leveraged small-cap with an armed dilution option, not a fortress.** ~4.0× at the top of management's stated 3.5–4.0× range, a $100M ATM in reserve, buybacks dormant. Issuing equity near 14× to buy 7–9× EBITDA deals is "accretive arithmetic" that masks an inability to self-fund growth. (In 2023, an informed strategic buyer bid ~$34/share all-cash and walked — public investors today pay well above that.)
5. **Category honesty:** Lynch's screen explicitly warns against acquisition-dependent growth + dilution. A "slow grower" whose appeal is supposed to be a fat, safe dividend instead pays ~1% — so there is no Lynch reason to *own* it here, only reasons to *watch* it cheaper.

**The skeptic leans Pass.** I land on a *cautious Watchlist* (below) because the underlying industry is genuinely defensive and the company is covenant-compliant, not in distress — but the bar to buy is high and currently failed on valuation, balance sheet, **and** decelerating organics.

## 7. Final checklist (ch. 15)
**Universal:**
- **P/E vs. growth:** PEG **2.80 (rich)** on ~5% (~1.9 on 7.4%); rich on every earnings base. ❌ (the decisive test)
- **Story:** clear and followable (defensive death-care). ✅
- **Institutional ownership:** ~73–78% — not crowded, room to be discovered. ✅ (mild)
- **Insider/buybacks:** insiders **net buying** ✅, but **$100M ATM = issuing** equity and buybacks dormant ❌ (net: a wash leaning negative).
- **Earnings record:** lumpy, one-off-distorted; organic growth modest and **volume declining**. ❌
- **Balance sheet:** **~4.0× leverage**, net debt ≈ ~$33 of a $45 share, **2029 refi into higher rates**. ❌ ("no debt can't go bankrupt" — this has a lot.)
**Slow-grower / valuation emphasis (the key issue is *price* + the dividend):** at PEG ~2.8 the price is **not reasonable**, and the ~1% dividend is no reason to own → **not a buy now**. The steady-growth premise is partly stalled (organic volume down). **Verdict: Watchlist.**

## 8. Verdict & sell triggers
**Verdict: Watchlist** — justified on fundamentals: a genuinely defensive, non-cyclical death-care niche, but **richly priced** (PEG ~2.8 on 5%, ~1.9 on 7.4% — rich even on adjusted/clean earnings) for a **single-digit, acquisition-dependent grower**, on a **leveraged balance sheet** (~4.0×, net debt ≈ ~$33/$45 share, $397M notes to refinance in 2029), with **declining organic funeral volume**, a **structural cremation headwind**, **ATM dilution**, and a **token ~1% dividend** that doesn't pay you to wait. Good-enough business, wrong price — the classic Watchlist case. *(The skeptic leaned Pass; this is a low-conviction Watchlist that effectively means "Pass at ~$45," not a "buy the dip" name. The price's recent rise is noted only because it makes the PEG richer — not as a reason in itself.)*

**Move to Buy candidate only if** (ideally all):
- **Price falls enough that PEG approaches ~1.0** on the *real* ~5–7% growth (a materially lower entry than $45);
- **Comparable funeral volume re-inflects positive** (organic growth, not just acquisitions);
- **Net leverage falls toward ~3.5×** without leaning on the ATM, **and** the 2029 notes are refinanced/paid on known terms;
- **Adjusted ≈ GAAP earnings** (the one-offs stop).

**Drop to Pass if** leverage rises toward the covenant, the ATM is used heavily to plug the balance sheet, or organic volume keeps declining while cremation mix climbs. Until a trigger fires: **watch, don't buy.**

## Sources
- Price $45.46 (2026-06-08) — [Investing.com](https://www.investing.com/equities/carriage-services-inc) / Yahoo / CNBC intraday (NYSE:CSV). Prior price $37.53 (2026-06-05) — [stockanalysis.com/stocks/csv](https://stockanalysis.com/stocks/csv/).
- EPS (FY2025 GAAP $3.25) + EPS history FY21–25 (1.81/2.63/2.14/2.10/3.25), dividend $0.45, shares 15,751,228, cash $1.688M, total debt $528.94M ($397.3M 4.25% Senior Notes due 2029 + $125.4M facility + acq. debt + current) — SEC EDGAR companyfacts / FY2025 10-K (CIK 0001016281), as of 2025-12-31 / 2026-02-19. [companyfacts](https://data.sec.gov/api/xbrl/companyfacts/CIK0001016281.json) · [FY2025 10-K](https://www.sec.gov/Archives/edgar/data/0001016281/000101628126000021/csv-20251231.htm).
- Computed metrics (P/E 13.99, PEG 2.80 on 5%, div-adj PEG 0.43, yield 0.99%, net cash −$527.25M / −$33.47/sh) — `compute_valuation.py` on `research/CSV.data.json` (validated by `validate_data.py`), 2026-06-08.
- Forward growth ~5% (conservative; co. guidance midpoint ~6%, consensus ~7.4%) — company FY2026 guidance / Simply Wall St / consensus, 2026-06-08. [stockanalysis forecast](https://stockanalysis.com/stocks/csv/forecast/) · [Simply Wall St](https://simplywall.st/stocks/us/consumer-services/nyse-csv/carriage-services/future).
- Institutional ~73–78%; insiders net buying; buybacks dormant + $100M ATM — [MarketBeat](https://www.marketbeat.com/stocks/NYSE/CSV/institutional-ownership/) · [SECForm4 (CIK 1016281)](https://www.secform4.com/insider-trading/1016281.htm) · [FY2026 Q1 10-Q](https://www.sec.gov/Archives/edgar/data/0001016281/000101628126000037/csv-20260331.htm).
- Q1 2026: comparable funeral volume −5.8% (10,663 vs 11,319), adj. EPS $0.86 vs $0.96 (−10.4%), GAAP $0.84 vs $1.34, revenue $106.1M vs $107.1M, FY26 guidance reaffirmed ($440–450M rev, $3.35–3.55 adj. EPS), leverage 4.0x — [StockTitan Q1-2026 release](https://www.stocktitan.net/news/CSV/carriage-services-announces-first-quarter-2026-results-and-confirms-0tb6jy4noc73.html).
- 2025: acquired 8 funeral homes + 1 cemetery + 1 cremation business in FL for $56.5M; FY2025 GAAP included divestiture gains, adjusted EPS growth ~21% — [StockTitan FY2025 release](https://www.stocktitan.net/news/CSV/carriage-services-announces-strong-fourth-quarter-and-full-year-2025-uplb8orfnc4h.html) · [Q4'25 call transcript](https://www.fool.com/earnings/call-transcripts/2026/04/21/carriage-csv-q4-2025-earnings-transcript/).
- 2029 refi context: BB US high-yield effective yield 5.85% (2026-06-04) — [YCharts](https://ycharts.com/indicators/us_high_yield_bb_effective_yield).
- Cremation ~63% (2025) → ~82% (2045) — NFDA cremation/burial report (per 2026-06-07 research).
- 2023 Park Lawn ~$34/share bid withdrawn — Funeral Director Daily (per 2026-06-07 research).
- Data file: `research/CSV.data.json` (validated by `validate_data.py`, computed by `compute_valuation.py`).
