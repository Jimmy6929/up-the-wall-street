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

These are **separate** tools. `/research` runs one ticker end-to-end (it *includes* a screening step), but it does **not** run `/screen`, `/recheck`, or `/portfolio-review` — those are standalone. `/scan` emits **leads, not verdicts** — it's a live discovery screen (survivorship/look-ahead biased by construction), never a backtester or a buy signal.

## The recommended way to use it

The agent is built around Lynch's actual rhythm: **find → investigate → decide → hold and re-check**. The human supplies the leads and the decisions; the agent supplies the discipline in between.

**1. Feed it leads — yours first.** Your real edge (ch. 06/12) is what you notice before Wall Street does: the product everyone at work uses, the packed store, the dull niche supplier. Jot those into `leads.md` in one line; no ceremony. When you have no leads, run `/scan` to sweep the market — but treat its ranked table as a *reading list*, not a buy list (the genuinely boring Lynch names often sit mid-table, and the manual-review bucket is worth mining).

**2. Triage cheaply before researching deeply.** Run `/screen` over `leads.md` (or a few tickers) to kill the obvious passes — hottest-in-hottest, "the next X", whisper stories — before spending a full research run. Expect most leads to die here. That's the system working.

**3. `/research` the survivors, then read two sections before anything else:** the **bear case** and the **category**. The category sets what you're allowed to expect (a stalwart is not a tenbagger; a cyclical's low P/E is a danger sign), and the bear case is the part you're most tempted to skip. Every number in the note carries a source and as-of date — if one doesn't, the run is broken; don't act on it.

**4. The verdict is the start of *your* work, not the end.** On a **Buy candidate**, the agent surfaces the mirror test (ch. 04) — can you hold through a 30–50% drawdown, is this money you won't need, can you ignore the price for years? It will never answer those for you, and it will never size a position. If you act, record it in `portfolio.md` so the monitoring tools can see it.

**5. Re-check the story, not the price.** Quarterly (or when earnings land), run `/recheck <TICKER>` — it re-runs the numbers and the three monitoring questions and decides Hold / Add / Sell *by category rules*. `scripts/verify` nags when a note hasn't been rechecked in ~100 days. Run `/portfolio-review` a couple of times a year for category balance, followability, and watering-the-weeds. The only valid reason to sell is a **broken story** — never "it's down", never "it's up", and a stock that's down 35% is not automatically a bargain.

**5b. Or let the watcher do the watching.** Each note's upgrade/re-examine triggers are compiled into `research/triggers.json`; `scripts/watch-triggers` polls SEC EDGAR (free) for exactly those events — new 10-K/10-Q/8-Ks, Form 4 *open-market buys*, the notes' valuation thresholds — and `scripts/watch-cron` (install one crontab line; see its header) auto-runs a headless `/recheck` on whatever fires, logs to `research/alerts.md`, and sends a Monday heartbeat so silence provably means "nothing happened". Lynch monitors events, not the screen — so the watcher does too.

**6. Don't ask it the questions it's designed to refuse.** "Where's the market headed", "is now a good time", options/shorting — it will decline and redirect to a researchable company (that's ch. 05 and ch. 19, not stubbornness). Pre-revenue lottery tickets get an honest "outside what the method can analyze."

### Keeping the agent trustworthy (maintenance)

| When | Run | Why |
|---|---|---|
| Before trusting the repo, or after touching scripts/data/notes | `scripts/verify` | Unit tests + the fail-closed schema/provenance gate + advisory note checks. Fast, free, offline. |
| After editing `playbook/`, skills, or scripts | `scripts/evals --smoke` | The method's regression test: re-runs the adversarial trap cases (cyclical peak, hot stock, whisper stock, derivatives, broken-story sell) headlessly and grades them. Costs real tokens. |
| Before trusting a big method change | `scripts/evals` | All cases at pass^3 — consistency, not best-of. |
| After any escalation or rubric edit (and ~monthly) | `/review-fixtures`, `/review-retro` | Recalibrates the self-review judges against the frozen fixtures; keep-or-revert. |
| Daily, unattended (cron) | `scripts/watch-cron` | Free EDGAR polling of every note's written triggers; headless `/recheck` only when one fires; Monday heartbeat. |

One habit ties it together: when a run surprises you (a data quirk, a near-miss, a source that disagreed), it appends one line to `research/lessons.md` — skim it occasionally; it's the agent's memory of where it almost went wrong.

### Using the watchlist monitor (`scripts/watch-*`)

The monitor is **not a background app** — nothing stays running between checks. Each run starts, polls the free SEC EDGAR API for the events your notes are waiting on (new 10-K/10-Q/8-Ks, Form 4 *open-market buys*, the notes' valuation thresholds from `research/triggers.json`), and exits in ~5 seconds. The LLM is involved **only** when a trigger fires (~8–12 events/year across a full watchlist) — quiet days cost $0.

**Run it by hand (no setup, safe anytime):**

```bash
scripts/watch-triggers --check     # poll now; prints "0 triggers fired" or 🔔 + details
scripts/watch-triggers --digest    # the one-line heartbeat (names watched, next known event)
cat research/alerts.md             # every alert ever fired (append-only record)
```

The very first `--check` *baselines*: it memorizes each ticker's existing filings without alerting, so history never floods you. When a trigger does fire, the next move is `/recheck <TICKER>` in a Claude Code session — a fired trigger is a reportable fact, **never a verdict**.

**Arm it (automatic weekday mornings):** add one line to your scheduler — `crontab -e`, then paste the line from the top of `scripts/watch-cron`. From then on macOS runs it at 08:30 on weekdays with **no Terminal window and no Claude session open** — `scripts/watch-cron` does the poll, auto-runs a headless `/recheck` on anything that fired, sends a desktop notification, and emits a Monday heartbeat. macOS caveat: plain cron **skips** a run if the Mac is asleep at 08:30 (alerts are delayed to the next run, never lost — filings don't expire); a launchd agent fixes this by running missed jobs on wake.

**How you know it's alive (when armed):**
1. the **Monday heartbeat** notification — its whole job is proving liveness;
2. `cat .watch-cron.log` — one entry per morning it actually ran;
3. `crontab -l` — the schedule entry exists;
4. `cat research/alerts.md` — what it has caught.

**Stop it:** `crontab -e`, delete the line, save — that's a complete stop. Nothing resides in memory, so there's no process to kill; the scripts go back to being inert files. (Unarmed — the state this repo ships in — there is nothing to stop: it runs only in the seconds after you type the command.)

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
