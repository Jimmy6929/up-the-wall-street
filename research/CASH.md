---
title: CASH — Pathward Financial
ticker: CASH
company: Pathward Financial, Inc.
type: research-note
category: Stalwart
verdict: Pass/Avoid
peg: 0.82
as_of: 2026-06-10
reviewed: 2026-06-10
tags: [research, stalwart]
---

# CASH — Pathward Financial

> [!summary] Verdict: **Pass/Avoid (for now)**
> The franchise is real (sponsor-bank rails, tax-refund season, −37% share count), but the "boring, well-run bank at 9.7x" story fails on its own filings: an accounting restatement with a **still-unremediated material weakness** (as of the Mar-2026 10-Q), organic net income flat-to-down with EPS growth manufactured by buybacks, guidance conditioned on "no rate cuts" (a rate forecast), and the screen's compound Avoid trigger (insider selling + 92.7% crowding). Re-examine when the controls are cured and net income — not just EPS — grows.

## 1. Lead (ch. 06)
From the 2026-06-10 `/scan` → qualitative screen (ranked #9; the screen's question was "do fees, not the rate cycle, carry the earnings?"). **Firsthand observation (ch. 12):** none — sourced from the screen/numbers.

## 2. Classification (ch. 07)
**Category:** Stalwart — mid-cap niche bank, real franchises, restated FY2021→25 EPS CAGR 15.8% decelerating to ~10–12% guided. (The scan's "35.6% CAGR fast grower" was a **data artifact** — `fetch_edgar.py` mis-framed this Sep-30 FYE filer, reading quarterly EPS as annual.)
**Expectation set:** stalwart — the question is price and earnings durability, not a tenbagger.

## 3. Screen (ch. 08–09)
- **Green flags:** dull name, dull business; genuine niches (BaaS sponsor banking, ~$11B/yr tax-refund processing); relentless buybacks (shares −37% in 5.5 years, EDGAR cover pages).
- **Red flags:** **restatement + ICFR material weakness still open**; insider selling (4 director sales in 5 months at descending prices, zero buys in 12 months) **plus** 92.7% institutional ownership — the screen's compound "strongly points to Avoid" pair; partner concentration (H&R Block flagship; Jackson Hewitt defected to a rival in 2022); two Nasdaq late-filing deficiency notices in 2025.
- **Excitement check:** no thrill in the story — the seduction here is the *multiple* (9.7x), which is the wrong reason to buy a bank with flat organic earnings.

## 4. The numbers (ch. 10–13) — *computed by `compute_valuation.py`*
| Metric | Value | Source | As of |
|---|---|---|---|
| Price | $81.55 | stockanalysis.com close | 2026-06-10 |
| EPS (ttm) | 8.41 | SEC EDGAR XBRL, script-computed TTM (FY2025 − H1 FY2025 + H1 FY2026) | 2026-03-31 |
| P/E | 9.7 | computed | 2026-06-10 |
| Earnings growth (hist.) | 15.8% | computed from restated EPS history (EDGAR FY2021–25) | FY2025 |
| Growth estimate (fwd) | 11.8% | management FY2026 guidance midpoint $8.80 vs FY2025 $7.87 (reaffirmed 2026-04-22); assumes **no rate cuts** | 2026-04-22 |
| **PEG** | 0.82 | computed | 2026-06-10 |
| Dividend-adj. PEG (g+y)/PE | 1.24 | computed | 2026-06-10 |
| Dividend yield | 0.25% | computed ($0.20/yr, flat since ≤FY2020) | FY2025 |
| Net cash (cash − debt) | n/m (financial) | bank: deposits are the funding base | 2026-03-31 |
| Institutional ownership | ~92.7% | MarketBeat 13F aggregate | ~2026-02 |
| Insider activity | selling; zero buys in 12 mo | SEC Form 4 via StockTitan / Sahm Capital (directors Perretta, Hajek, Hoople; $82–94 range) | 2026-05-29 |
| Buybacks | shares −37% in ~5.5 yrs | SEC EDGAR dei cover pages, 33.45M → 21.11M | 2026-04-29 |
| Earnings mix (fee vs NII) | 39.1% fee FY2025; 45.6% H1 FY2026 | SEC EDGAR XBRL (NoninterestIncome / Revenues), script-computed | 2026-03-31 |

**Read:** PEG 0.82 fired `peg_attractive` — but the G is mostly buyback-and-rate-assumption, not organic growth: fiscal Q2 2026 (the tax quarter) **net income fell 2.8%** while EPS rose on a −9.7% share count. `crowded_ownership` and `insider_selling` also fired.

## 5. The two-minute drill (ch. 11)
1. **What it is:** the bank behind other people's products — it sponsors fintech card programs and processes tax-refund advances, funding itself with near-free partner deposits.
2. **Why it grows:** partner pipeline + the March tax season (~⅔ of H1 profit), with buybacks converting flat earnings into per-share growth.
3. **What breaks it:** rate cuts compressing NII (61% of revenue) with no funding offset; a flagship tax partner defecting (precedent exists); BaaS regulatory tightening ("just getting started" — the CEO's own words); the controls problem becoming an OCC problem.

## 6. Bear case (the skeptic, ch. 09/20)
The skeptic broke the thesis as drafted: a sponsor bank's entire product is *operational competence over third parties*, yet Pathward restated its own third-party-lending accounting back to Dec-2021, drew two Nasdaq deficiency notices for late 10-Qs in 2025, and the material weakness was **still unremediated in the 10-Q filed 2026-05-07**. Organic earnings are flat (Q2 FY2026 net income −2.8% in the tax quarter; NII −8%; NIM 6.63% vs 7.12%), so the +11.8% "growth" in the PEG is share-count arithmetic conditioned on an explicit no-rate-cut assumption — an embedded rate forecast the method refuses to make (gate 1). Concentration is in the company's own risk factors ("a limited number of program manager relationships"). Honest concessions: no securities litigation or enforcement found; the restatement was presentational (−$17.4M retained earnings, ~1% of equity), not a credit event; the tax franchise genuinely performs (H1 tax revenue +13%).

## 7. Final checklist (ch. 15)
- Universal: P/E vs growth ✓ on paper, ✗ in substance (growth is buybacks + a rate assumption) · story ~ (real niches, impaired execution claim) · ownership ✗ (92.7%) · insiders ✗ (selling, no buys) · earnings record ✗ (restated; organic NI flat) · balance sheet ~ (bank-normal; controls weakness is the issue).
- Stalwart specific: is the price right for the durability? A 9.7x multiple is not cheap for flat organic earnings with an open material weakness — there's no margin of safety in a multiple alone.

## 8. Verdict & sell triggers
**Verdict:** **Pass/Avoid (for now)** — justified by fundamentals: the screen's compound Avoid trigger (insider selling + crowded register) fires on top of an unremediated control weakness and organic earnings that don't grow; the cheap P/E is the bait, not the case. This is a *quality-of-evidence* Pass, not a forever-no.
**Re-examine when (set in advance):** (1) the FY2026 10-K (Nov 2026) declares ICFR effective with auditor concurrence; (2) two consecutive quarters of **net income** (not EPS) growth; (3) partner/deposit concentration quantified from the 10-K and the H&R Block relationship term confirmed; (4) any open-market insider buy. All four are reportable facts — no forecasting required.

## Sources
- SEC EDGAR companyfacts CIK0000907471 (restated EPS history, shares, TTM build; 10-K filed 2025-11-25, 10-Q filed 2026-05-07)
- Pathward 10-K/A (Aug 2025 restatement) + FY2025 10-K (material weakness; risk factors)
- stockanalysis.com CASH quote (close, 2026-06-10)
- Q2 FY2026 results, Business Wire / StockTitan (net income, NIM, buyback price; 2026-04-22)
- Q1 FY2026 earnings call transcript, Motley Fool (guidance assumptions; 2026-01-23)
- MarketBeat / Fintel (institutional ownership)
- SEC Form 4 via StockTitan / Sahm Capital / Daily Political (director sales, through 2026-05-29)
- Nasdaq deficiency notices, Business Wire / StockTitan (May & Aug 2025)
- Banking Dive (CEO Pharr on BaaS regulatory scrutiny)
