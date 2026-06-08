# 03 — The Numbers (ch. 10, 12, 13)

> [!important] Do not compute these in your head.
> Finance is where language models hallucinate most convincingly. **Run `compute_valuation.py`** on the assembled data and read its output. Every figure in the final note must carry a **source + as-of date**. If a required number is missing, get it ([12 — Getting the Facts] path: SEC EDGAR script → web search → ask the user) — do not guess.

**Earnings drive prices.** Over time a stock's price follows its earnings. So the core questions are: how fast are earnings growing, how durable is that growth, and what are you paying for it?

## Getting the facts (ch. 12) — the source ladder

Before the numbers can be computed, they have to be *gotten* — and where you get them is itself part of Lynch's edge. Two ladders, used together:

- **Hard figures (what the scripts need):** SEC EDGAR script → web search → ask the user to paste. This is the deterministic path; every figure records its source + as-of date, and a missing figure is stated, never guessed.
- **Lynch's own legwork (the amateur's advantage):** the **annual report / 10-K** (read it, especially the footnotes and the balance sheet), **investor relations** (you can literally call and ask why earnings grew), and **kicking the tires** — your own firsthand observation of the product, the store, the parking lot, people in the industry. This is the firsthand evidence captured in the [Lead step](../.claude/skills/research/SKILL.md) (ch. 06): note what *you* can see that the screen can't. It is legitimate for this to be "none — sourced from the screen/numbers"; Lynch finds names both ways. But when firsthand evidence exists, it is a real input, not decoration.

## The numbers that matter (and how to read them)

### P/E ratio — the price of earnings
`P/E = price ÷ EPS(ttm)`. How many years of current earnings you're paying. Compare to the company's own history, its industry, and the market.

### PEG — P/E vs. growth rate (Lynch's signature tool)
`PEG = P/E ÷ earnings-growth-rate(%)`.
- **PEG ≈ 1** → fairly priced.
- **PEG ≈ 0.5** (P/E ≈ half the growth rate) → very attractive / bargain.
- **PEG ≈ 2** (P/E ≈ twice the growth rate) → overpriced, headed for a comedown.

A raw P/E is incomplete: a P/E of 20 is expensive for a 10% grower and cheap for a 40% grower. PEG fixes that.

### Dividend-adjusted PEG (the refined version)
`(long-term growth rate + dividend yield) ÷ P/E`.
- **< 1** → poor. **1.5** → okay. **≥ 2** → what you really want.
- Example: a 12% grower paying a 3% dividend at a P/E of 10 → (12 + 3) / 10 = **1.5** (okay).

### Cash and debt
- **Net cash = cash − total debt.** A strong net-cash position is a cushion and hidden value (sometimes cash/share is a big fraction of the price).
- **"A company with no debt can't go bankrupt."** Balance-sheet strength is central, especially for turnarounds. Note the *kind* of debt (funded vs. bank debt that can be called).

### Dividends
Whether it pays one and has reliably *raised* it over decades. Payers (slow growers, stalwarts) offer downside support; non-payers reinvest for growth. Either can be right — check the long record.

### Book value — handle with care
Stated book value misleads both ways: assets may be worth far *less* (obsolete inventory) or far *more* (undervalued real estate — the basis of asset plays). Hunt for *hidden* assets the book understates.

### Cash flow & inventories
- Prefer companies that don't need heavy capital spending to produce their cash (free cash flow > cash flow that must be plowed back).
- **Inventories:** piling up faster than sales is a warning; bloated inventories shrinking can signal a recovery. (For cyclicals, rising inventories near a peak is a sell signal.)

### Earnings growth rate — the number that ultimately moves the stock
Of all growth measures, **earnings** growth is the one that drives the price. Compute the historical rate from the EPS history; pair it with a forward estimate, and **favor proven growth over hoped-for growth** ("as to the all-important future growth rate, your guess is as good as mine").

## The cyclical caveat (critical)
For a **cyclical**, PEG and a low P/E are *misleading*. A low P/E on **peak** earnings is a **danger sign** — the market is pricing in the coming fall. Do not treat a cyclical at the top as a bargain. (See [01 — Classify](01-classify.md) and [05 — Checklist](05-checklist.md).)

## Output of this step — `research/<TICKER>.data.json`
Assemble the raw inputs (each with a source + as-of date), then run the scripts. Required fields:
- `price`, `eps_ttm`, `eps_history` (multi-year), `dividend_per_share`, `shares_outstanding`, `total_debt`, `cash`, `long_term_growth_estimate_pct`, `institutional_ownership_pct`, `insider_activity`, `buybacks`.
- The script returns: `pe`, `historical_growth_pct`, `peg`, `dividend_adjusted_peg`, `dividend_yield_pct`, `net_cash`, `net_cash_per_share`, plus `flags` (e.g., cyclical-caveat, negative-earnings, unsustainable-growth) and a `provenance` echo.
