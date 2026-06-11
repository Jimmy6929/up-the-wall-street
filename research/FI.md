---
title: FI — Fiserv (formerly FISV)
ticker: FI
company: Fiserv, Inc.
type: research-note
category: Turnaround
verdict: Watchlist
peg: n/a
as_of: 2026-06-10
reviewed: 2026-06-10
tags: [research, turnaround]
---

# FI — Fiserv (formerly FISV)

> [!summary] Verdict: **Watchlist**
> The turnaround's survival half passes (no acute debt wall, $4.4B FCF, investment grade affirmed); the recovery half is **not yet evidenced — the latest quarter argues against it** (organic revenue −4%, margins down ~800–900 bps, the stable segment guided worse). Lynch bought Chrysler when the recovery was visible, not promised. Watch the five evidence triggers; re-review after Q2 2026 results (early August).

## 1. Lead (ch. 06)
From the 2026-06-10 `/scan` → qualitative screen ("busted stalwart — research under turnaround rules"). **Firsthand observation (ch. 12):** none — sourced from the screen/numbers. Note: the scan's price row was suspect (stale FISV ticker); every figure here was re-sourced by hand.

## 2. Classification (ch. 07)
**Category:** Turnaround (busted stalwart) — a payments giant whose guidance collapsed in 2025; the question is survival first, then whether recovery is real. **Not** a fast grower: the GAAP EPS "CAGR" of 33.6% is First Data amortization roll-off fiction, and ~10 points of 2024's "organic growth" was Argentine inflation effects.
**Expectation set:** turnaround — judged on the balance sheet and evidence of the turn, never on the size of the drawdown (a low price is not a floor, gate 2).

## 3. Screen (ch. 08–09)
- **Green flags:** dull, hated, and ignored — the right *shape* for a turnaround; repeat-purchase processing revenue; genuine open-market insider buying into the crash (director Fritz 10k sh @ $65.18; CFO Todd 17k sh @ $62.41; CALO Rosman 7.9k sh @ $63.19 — all above today's price); shares −18.3% in 4 years.
- **Red flags:** crowded register (91.6% institutional) still distributing; securities class action alleging ~200k Payeezy merchants force-migrated and booked as Clover growth; congressional SEC referral over the ex-CEO's ~$457M+ of pre-crash sales; management almost entirely new (CEO May-2025, CFO Oct-2025); buybacks were partly debt-funded at 2–4x today's price; S&P outlook Negative (2026-02-05).
- **Excitement check:** the case isn't thrilling — but the skeptic caught the subtler tell: anchoring on "down 75%" is price-action reasoning (gate 2) and plays no role in this verdict.

## 4. The numbers (ch. 10–13) — *computed by `compute_valuation.py`*
| Metric | Value | Source | As of |
|---|---|---|---|
| Price | $53.28 | stockanalysis.com close (hand-sourced; no yfinance) | 2026-06-10 |
| EPS (ttm, GAAP) | 5.91 | stockanalysis.com TTM; FY2025 GAAP 6.34 per EDGAR 10-K (GAAP includes heavy intangible amortization) | 2026-06-10 |
| P/E (GAAP ttm) | 9.02 | computed | 2026-06-10 |
| Adjusted EPS (FY2025) | 8.64 (−2%, first decline) | company Q4/FY2025 release (non-GAAP) | 2026-02-10 |
| Earnings growth (hist., GAAP) | 33.6% | computed — **amortization-inflated; do not extrapolate** (script's own warning) | FY2021–25 |
| Growth estimate (fwd) | −5.7% | guided 2026 adj EPS midpoint $8.15 vs FY2025 $8.64 (script-computed; reaffirmed 2026-05-05) | 2026-05-05 |
| **PEG** | n/a | computed: null — guided growth is negative; PEG is meaningless for this turnaround | 2026-06-10 |
| Dividend yield | 0.0% | computed (no dividend) | FY2025 |
| Net debt | −$28.4B (−$53.17/sh) | computed (EDGAR: $29.18B debt, $0.83B cash) — roughly the share price | 2026-03-31 |
| Debt due ≤2 yrs | $4.04B | SEC EDGAR FY2025 10-K maturity tags — vs $4.44B FY2025 FCF; big tower ($6.04B) in year 5 | 2025-12-31 |
| Interest coverage | 3.80x | computed: EDGAR FY2025 operating income $5,818M / interest $1,531M | FY2025 |
| Free cash flow | $4.44B (was $5.23B) | company FY2025 release; EDGAR cross-check OCF−capex = $4.30B | FY2025 |
| 2026 guidance | organic +1–3%; adj EPS $8.00–8.30 | Q4/FY2025 release 2026-02-10, reaffirmed 2026-05-05 (Q1 actual: organic −4%, adj EPS −16%) | 2026-05-05 |
| Institutional ownership | ~91.6% | Fintel 13F aggregate | 2026-06-10 |
| Insider activity | 3 open-market buys Oct–Dec 2025 ($62–65); ex-CEO sold $457M+ pre-crash (ethics-mandated; timing under SEC referral) | SEC EDGAR Form 4 XMLs, parsed directly; StockTitan Form 144 | 2026-03-31 |

**Read:** PEG null is the honest output — there is no growth to pay for yet. The survival math is the usable part: $4.04B due through 2027 against $4.44B of annual FCF, coverage 3.8x. At ~6.5x guided adjusted EPS the *price* assumes recovery; the *filings* don't show one yet.

## 5. The two-minute drill (ch. 11)
1. **What it is:** plumbing for money — card processing for banks (Financial Solutions) and point-of-sale for merchants (Clover), billions of transactions on contract.
2. **Why it recovers (the claim):** guidance reset to a low bar (+1–3% organic), Argentina distortions lap out of the comps, "One Fiserv" integration stabilizes Clover, and $4B+ of FCF funds the repair without dilution.
3. **What breaks it:** Clover structurally losing merchants to Toast/Square (Clover +6% in Q1 2026 vs Toast +24%); Financial Solutions attrition to Jack Henry/FIS (−6% Q1); margins not troughing as promised; EBITDA down 10–20% would push coverage toward ~3x and leverage into downgrade territory with a year-5 tower to refinance.

## 6. Bear case (the skeptic, ch. 09/20)
The skeptic's strongest case: **this prices a recovery the most recent quarter affirmatively contradicts.** Q1 2026: organic −4% (both segments negative), adjusted EPS −16%, margins down 780–940 bps — and the "affirmed" +1–3% guide arithmetically requires an H2 hockey stick from a CFO with two quarters of tenure, whose predecessors' "16% organic growth" included ~10 points of Argentine hyperinflation and force-migrated merchants now in securities litigation. FCF is a falling number quoted as a stable one ($5.23B → $4.44B → ~$4.0B guided), likely flattered by underinvestment — the margin collapse is that bill coming due. The insider buys are real but ~200:1 outweighed by the ex-CEO's pre-crash sales, and the current CEO is conspicuously not among the buyers. Conceded by the skeptic: the balance sheet survives (no acute wall, IG affirmed), the story is correctly dull and hated, and the category claim (turnaround) is right — only the *timing* claim fails.

## 7. Final checklist (ch. 15)
- Universal: P/E vs growth ✗ (no growth yet; PEG null) · story ~ (coherent recovery claim, zero quarters of evidence) · ownership ✗ (91.6%) · insiders ~ (genuine buys vs massive prior sales) · earnings record ✗ (adjusted EPS declining) · balance sheet ✓ for survival, ✗ for comfort ($28.4B net debt ≈ market cap).
- Turnaround specific: **Can it survive?** Yes — $4.04B ≤2yr maturities vs $4.44B FCF, coverage 3.8x, IG affirmed. **Is the recovery real?** Not yet — organic revenue still shrinking, margins still falling, guidance untested. Lynch's rule: buy turnarounds on evidence, not on promises.

## 8. Verdict & sell triggers
**Verdict:** **Watchlist** — justified by fundamentals: survival is established, recovery is not. The price may well be lower or higher when the evidence arrives; the evidence, not the price, is the trigger.
**Upgrade triggers (evidence, set in advance — first checkpoint Q2 2026 results, early August):** (1) two consecutive quarters of positive total organic growth with Argentina lapped; (2) Clover merchant counts and revenue rising *together*, churn stabilizing vs Toast/Square; (3) margins recovering toward guide while capex stays at investment-year levels; (4) FCF ≥ ~$4B with net debt flat-to-down and buybacks deprioritized below ~2.5x leverage; (5) S&P outlook back to Stable — and ideally an open-market buy by the sitting CEO.
**Drop-the-watch triggers:** another guidance cut; Financial Solutions organic decline worsening past the guided trough; a downgrade to BBB− with negative outlook.

## Sources
- SEC EDGAR companyfacts/submissions CIK0000798354 (GAAP EPS history, debt, maturities, coverage inputs, shares, Form 4 XMLs)
- stockanalysis.com FI quote (close + GAAP TTM EPS, 2026-06-10)
- Fiserv Q4/FY2025 results, GlobeNewswire/SEC 8-K (adj EPS, FCF, guidance; 2026-02-10)
- Fiserv Q1 2026 results + call transcript, Motley Fool / StockTitan / Investing.com (organic −4%, margins, reaffirmation; 2026-05-05)
- Fiserv Q4 2024 8-K + Q2 2024 call (Argentina contribution to "organic" growth)
- Payments Dive / Rosen Law (Clover migration class action)
- S&P Global Ratings (outlook Negative, 2026-02-05); Moody's (Baa2 affirmed, Nov 2025)
- StockTitan Form 144 + larson.house.gov (ex-CEO sales; SEC referral)
- Fintel (institutional ownership, 2026-06-10)
