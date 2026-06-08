# Up the Wall Street

A markdown-driven research agent that **thinks and acts like Peter Lynch's _One Up on Wall Street_**.

The agent's reasoning lives in markdown — a stack of `playbook/` files (the method), surfaced as Claude Code skills and subagents — not in hardcoded logic. You can change how it thinks by editing prose. The only code is a thin, deterministic seam that fetches and computes the numbers, because finance is exactly where language models hallucinate most convincingly.

> [!warning] What this is and isn't
> This is a **disciplined research assistant** that enforces Lynch's process and always surfaces a bear case. It is **not** financial advice, a price forecaster, or a trading bot. It produces theses and Buy/Watch/Pass verdicts as markdown notes; a human decides and trades. Research consistently finds that LLM "stock-picking edge" largely disappears over long horizons — Lynch's own refusal to forecast (ch. 05) is baked in on purpose.

## How it works

Every stock runs through Lynch's pipeline, in order:

1. **Gate** (ch. 00–05, 19) — refuse market timing; judge the business, not the price; a lead is not a buy signal; decline derivatives and redirect to the underlying.
2. **Classify** (ch. 07) — sort into one of the [Six Categories](playbook/01-classify.md); a giant can't be a tenbagger.
3. **Screen** (ch. 08–09) — green flags vs. red flags; excitement is a *yellow* flag.
4. **Numbers** (ch. 10–13) — fetched and computed by code, never by the model: PEG, dividend-adjusted PEG, cash vs. debt, earnings record. Every figure carries a **source + as-of date**.
5. **Story** (ch. 11) — the category-specific two-minute drill.
6. **Skeptic** (ch. 09/20) — an independent agent tries to refute the thesis.
7. **Verdict** (ch. 15) — a category-specific checklist → Buy candidate / Watchlist / Pass.
8. **Monitor** (ch. 14/17) — `/recheck` re-runs the story; sell only when it breaks, never on price/fear/boredom.

The chapter→step mapping (gates / pipeline / ongoing) is tracked as a living artifact in [`playbook/00a-book-map.md`](playbook/00a-book-map.md) and enforced by `tests/test_book_map.py`, so a chapter can't silently lose its home.

## Usage

In Claude Code, **launched from this repo**, run a slash command — or just ask in plain English (the method in `CLAUDE.md` + `playbook/` governs either way):

| Command | What it does |
|---|---|
| `/research <TICKER>` | The full pipeline for **one** stock: classify → screen → script-computed numbers → two-minute story → skeptic/bear case → Buy / Watch / Pass verdict. Writes `research/<TICKER>.md` (+ `.data.json`). |
| `/scan [tickers]` | Scan the **whole US market** (or a subset) for candidates: a deterministic EDGAR funnel ranks names by PEG, then a parallel green/red-flag screen recommends 1–3 for `/research`. Writes `scan-results.md`, appends *leads* (never verdicts) to `leads.md`. See [playbook/02a](playbook/02a-screen-at-scale.md). |
| `/screen [tickers]` | Quick green-flag / red-flag triage over `leads.md` (or the tickers you pass) to decide what deserves a full run. |
| `/recheck <TICKER>` | Re-test a holding's story, refresh the numbers, run the 3 monitoring questions → Hold / Add / Sell. Updates `watchlist.md` / `portfolio.md`. |
| `/portfolio-review` | Whole-portfolio check: category balance, followability, watering-the-weeds, concentration, stale stories. |

These are **separate** tools. `/research` runs one ticker end-to-end (it *includes* a screening step), but it does **not** run `/screen`, `/recheck`, or `/portfolio-review` — those are standalone. Typical cadence: `/scan` the market (or jot ideas in `leads.md`) → `/screen` to triage → `/research` the survivors → `/recheck` holdings (quarterly) → `/portfolio-review` for balance. `/scan` emits **leads, not verdicts** — it's a live discovery screen (survivorship/look-ahead biased by construction), never a backtester or a buy signal.

## Layout

```
playbook/         the method, as editable markdown (the "Gstack")
playbook/00a-book-map.md   chapter→step traceability (gates/pipeline/ongoing), test-enforced
templates/        research-note template (every number cites a source)
evals/            labeled cases the agent must pass (incl. adversarial traps)
.claude/skills/   the pipeline + scripts, surfaced as slash commands
.claude/agents/   numbers-analyst (data) and skeptic (bear case)
research/         output: one note + one .data.json per ticker
watchlist.md      leads under consideration
portfolio.md      recommended theses
leads.md          raw idea intake (ch. 06)
scan-results.md   latest full-universe /scan output (ranked candidates + manual-review + tallies)
scan-results.fixtures.md   offline --fixtures verification output (never overwrites the real sweep)
tests/fixtures/   offline records for the screener's trap tests
scripts/verify    one local gate: tests + schema/provenance + markdown source coverage
```

### Scan artifacts (fixed names, never crossed)

A full-universe `/scan` writes **`scan-results.md`**. An offline `--fixtures` verification run writes **`scan-results.fixtures.md`** — it is offline by contract and must **never** clobber the real sweep's `scan-results.md` (regression-pinned by `tests/test_universe_screen.py`). `scan-results.sample.md` is reserved for a future small live sample (no `--sample` mode today).

### Verifying the repo

Run **`scripts/verify`** before trusting the repo (or after touching scripts, data, or notes). It runs the unit-test suites (both roots), the bulk **schema/provenance gate** (`validate_data.py research/*.data.json`, which *fails closed* — a `.data.json` with a missing required field or an unsourced value cannot pass), and an advisory **markdown source/as-of coverage** check (`check_research_markdown.py`). Tests + schema block; markdown is warn-only until tuned.

## Setup

- **Python 3.10+** — the `/research` scripts (`fetch_edgar.py`, `compute_valuation.py`, `validate_data.py`) and all tests use only the standard library (no `pip install`). The **one** exception is `/scan`: `universe_screen.py` optionally uses `yfinance` for bulk prices (`pip install -r requirements.txt`); it's a lazy import and the screen degrades gracefully without it.
- **Data:** `fetch_edgar.py` pulls exact figures directly from the free [SEC EDGAR API](https://www.sec.gov/edgar/sec-api-documentation) (no key needed; SEC requires a contact string — set yours in `.mcp.json` / when prompted). Live prices come from web search. For the `/scan` funnel only, yfinance supplies bulk prices — **screening-only**, never cited as the price in a `/research` note (finalists are re-sourced by hand). Anything missing, you can paste in.
- **Optional:** the [`sec-edgar-mcp`](https://github.com/stefanoamorelli/sec-edgar-mcp) server (configured in `.mcp.json`) lets the agent also read filing *text* and insider transactions interactively. It needs [`uv`](https://docs.astral.sh/uv/) (`uvx`). The deterministic script works without it.

## Provenance

The method is compiled from notes on _One Up on Wall Street_ (Peter Lynch with John Rothchild, 1989 / Millennium Edition 2000). The numeric discipline (script-computed metrics, sourced figures, mandatory bear case) follows current guidance on building reliable agents — see the plan's source list.
