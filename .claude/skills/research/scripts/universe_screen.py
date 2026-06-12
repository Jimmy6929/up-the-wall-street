#!/usr/bin/env python3
"""universe_screen.py - the market-wide front-end of the Lynch funnel.

Turns "the whole US market" into a short, ranked list of *candidates* (leads),
so the human is no longer the bottleneck that has to know the ticker first. It
is a SCREEN, not a verdict-generator: it emits numbers + a category *guess* and
never a Buy/Watch/Pass. The qualitative judgment (green/red flags, story, bear
case, verdict) stays in the markdown skills (/screen, /research).

The funnel:
  Stage A (free, SEC EDGAR `frames`, no price): one call per concept returns
    that concept for every filer; keep names with positive, consistent,
    multi-year diluted EPS. Drops ~90%. Frames are a *filter only* - their
    calendar/fiscal "best-fit" values never appear in the output.
  Stage B (survivors only, + yfinance price): re-fetch each survivor's exact
    `companyfacts`, compute TTM EPS (sum of 4 quarters, FY fallback), attach a
    yfinance price stamped with its REAL quote date, and run the shared
    compute_valuation.compute() for PEG / net cash.
  Ranking: only non-cyclical, positive-earnings names are ranked by PEG.
    Cyclicals/erratic/dual-class/unsustainable -> a separate "Manual review"
    section (a low P/E on a peak-earnings cyclical is a trap, ch.15). The script
    CANNOT detect a monotone-up cyclical from EPS alone - that defense lives in
    the qualitative /screen step, and the playbook says so.

This is a LIVE DISCOVERY SCREEN, NOT A BACKTESTER. The universe is only
currently-listed filers (survivorship bias) using latest/restated values
(look-ahead bias). Fine for "what should I look at today"; it makes no
performance claim.

Usage:
    python3 universe_screen.py --tickers AAPL,KO,XOM      # subset (dev/live)
    python3 universe_screen.py                            # full universe (frames)
    python3 universe_screen.py --fixtures tests/fixtures  # offline, no network
    python3 universe_screen.py --no-price                 # Stage A quality only
"""
import argparse
import datetime
import glob
import json
import os
import sys
import time

# The deterministic seam - reuse, never re-implement, the EDGAR I/O and the math.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_edgar as fe                                          # noqa: E402
from compute_valuation import compute, cagr_pct, UNSUSTAINABLE_GROWTH  # noqa: E402

try:                    # yfinance is an OPTIONAL, screening-only price source.
    import yfinance as yf
except ImportError:
    yf = None

FRAMES_URL = "https://data.sec.gov/api/xbrl/frames/us-gaap/{concept}/USD-per-shares/CY{year}.json"

# --- screen thresholds (named, documented - same spirit as compute_valuation) ---
MIN_YEARS = 4            # need >= this many positive annual EPS points in the window
CYCLICAL_DROP_PCT = 20   # any single-year EPS drop > this -> possible_cyclical -> manual
SLOW_MAX = 5             # CAGR < 5%        -> Slow grower
STALWART_MAX = 15        # 5-15%            -> Stalwart
FAST_MIN = 20            # >= 20%           -> Fast grower (5-20% gap -> "Moderate grower")
# CAGR >= UNSUSTAINABLE_GROWTH (50, imported) -> manual review (rarely sustainable)
PER_SHARE_BAND = (0.6, 1.6)   # NI/shares vs reported FY EPS: outside this band the
#   share count doesn't match the EPS basis (dual-class line, big NCI, wrong share
#   tag) and EVERY per-share number is suspect -> manual. Wide on purpose: it must
#   tolerate weighted-average-vs-point-in-time share counts and dilution, and only
#   catch basis errors (which are ~2x+), never ordinary buybacks.

# A bank's/insurer's cash - debt is NOT Lynch net cash: deposits, reserves and
# policy liabilities are operating liabilities, so the figure is meaningless
# (the BFC "-3510.94/sh" artifact). Any of these us-gaap tags marks a financial.
FINANCIAL_TAGS = ("Deposits", "InterestAndDividendIncomeOperating",
                  "LiabilityForFuturePolicyBenefits", "PolicyholderContractDeposits",
                  "SeparateAccountAssets")

DISCLAIMER = ("Live discovery screen, NOT a backtester. Survivorship + look-ahead "
              "biased by construction (currently-listed filers, latest/restated "
              "figures). Candidates are NOT verdicts and NOT a buy signal - run "
              "/screen then /research. No performance claim is made.")


# --------------------------------------------------------------------------- #
# Classification + gates (the discipline layer)
# --------------------------------------------------------------------------- #
def band(cagr):
    """Lynch category *guess* from the historical EPS CAGR (ch.07). A guess only -
    the qualitative skill re-classifies (size, cyclicality, hidden assets)."""
    if cagr < SLOW_MAX:
        return "Slow grower"
    if cagr < STALWART_MAX:
        return "Stalwart"
    if cagr < FAST_MIN:
        return "Moderate grower"
    return "Fast grower"


def gate(rec, years):
    """Return (disposition, category_guess, reason) from the numbers alone.

    disposition: 'ranked' (rank by PEG) | 'manual' (set aside for a human) |
    'dropped' (out of mechanical scope). Honors classify-before-rank and the
    cyclical/peak-PE trap as far as EPS allows - see the module docstring on the
    monotone-cyclical limit."""
    hist = rec.get("eps_history") or {}
    try:
        pts = sorted((int(y), float(v)) for y, v in hist.items())
    except (ValueError, TypeError):
        pts = []
    recent = pts[-years:]
    eps_ttm = rec.get("eps_ttm")

    if eps_ttm is None or len(recent) < 2:
        return "dropped", None, "insufficient EPS data"
    if eps_ttm <= 0:
        return "dropped", None, "negative or zero TTM EPS (pre-revenue / turnaround)"
    if len(recent) < MIN_YEARS:
        return "manual", None, f"insufficient EPS history (<{MIN_YEARS} of {years} yrs)"
    if any(v <= 0 for _, v in recent):
        return "manual", None, "negative earnings year in window"
    if (rec.get("n_share_classes") or 1) > 1:
        return "manual", None, "multi-class shares (per-share math unreliable)"
    if rec.get("per_share_check"):
        return "manual", None, f"per-share math inconsistent ({rec['per_share_check']})"
    for (y0, v0), (y1, v1) in zip(recent, recent[1:]):
        if v0 > 0 and (v1 - v0) / v0 < -CYCLICAL_DROP_PCT / 100:
            return "manual", None, f"possible_cyclical (EPS dropped >{CYCLICAL_DROP_PCT}% in {y1})"
    cagr = cagr_pct({str(y): v for y, v in recent})
    if cagr is None:
        return "manual", None, "growth not computable"
    if cagr >= UNSUSTAINABLE_GROWTH:
        return "manual", None, f"unsustainable growth (~{cagr:.0f}%/yr) - needs a human"
    return "ranked", band(cagr), None


def _to_facts(rec):
    """Shape a record for compute_valuation.compute() (it unwraps plain values)."""
    return {
        "price": rec.get("price"),
        "eps_ttm": rec.get("eps_ttm"),
        "eps_history": rec.get("eps_history"),
        "dividend_per_share": rec.get("dividend_per_share", 0) or 0,
        "shares_outstanding": rec.get("shares_outstanding"),
        "total_debt": rec.get("total_debt", 0) or 0,
        "cash": rec.get("cash", 0) or 0,
        "long_term_growth_estimate_pct": rec.get("long_term_growth_estimate_pct"),
    }


def screen_one(rec, years):
    """Gate then (for ranked names) value. A ranked name with no price is dropped
    and counted - it is never ranked on a guessed/stale price."""
    disp, cat, reason = gate(rec, years)
    if disp != "ranked":
        return {"rec": rec, "disposition": disp, "category": cat, "reason": reason, "metrics": None}
    price = rec.get("price")
    if price is None or price <= 0:            # a 0/negative quote must never rank
        return {"rec": rec, "disposition": "dropped", "category": cat, "reason": "no price", "metrics": None}
    # category guess is never 'cyclical' (we can't tell from numbers), so compute
    # never applies the cyclical caveat here - that judgment is deferred.
    metrics = compute(_to_facts(rec), cat)
    return {"rec": rec, "disposition": "ranked", "category": cat, "reason": None, "metrics": metrics}


def screen_records(records, years=5):
    """Screen a list of records into ranked / manual / dropped, with reasoned
    tallies. The single place ranking discipline is applied."""
    ranked, manual, dropped_counts, dropped_detail = [], [], {}, []
    for rec in records:
        res = screen_one(rec, years)
        if res["disposition"] == "ranked":
            ranked.append(res)
        elif res["disposition"] == "manual":
            manual.append(res)
        else:
            dropped_counts[res["reason"]] = dropped_counts.get(res["reason"], 0) + 1
            dropped_detail.append(res)
    # rank by plain PEG ascending; None PEG (e.g. growth<=0) sorts last.
    ranked.sort(key=lambda r: (r["metrics"].get("peg") is None, r["metrics"].get("peg")))
    return {"ranked": ranked, "manual": manual,
            "dropped_counts": dropped_counts, "dropped_detail": dropped_detail,
            "n_in": len(records)}


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def _prov(rec, kind):
    src = rec.get(f"{kind}_source") or "?"
    asof = rec.get(f"{kind}_as_of") or "?"
    return f"{src} ({asof})"


def render_scan_results(result, date_str):
    L = [f"# Scan results - {date_str}", "",
         f"> [!warning] {DISCLAIMER}", "",
         f"Screened {result['n_in']} names -> "
         f"{len(result['ranked'])} ranked candidates, "
         f"{len(result['manual'])} manual-review, "
         f"{sum(result['dropped_counts'].values())} dropped.", ""]

    L += ["## Ranked candidates (by PEG - NOT verdicts)", "",
          "| # | Ticker | Company | Category (guess) | CAGR% | P/E (TTM) | PEG | div-adj PEG | Net cash/sh | Flags | Price src | Fundamentals src |",
          "|---|--------|---------|------------------|-------|-----------|-----|-------------|-------------|-------|-----------|------------------|"]
    for i, r in enumerate(result["ranked"], 1):
        rec, m = r["rec"], r["metrics"]
        flags = ", ".join(f for f in m.get("flags", []) if f not in ("no_debt",)) or "-"
        # cash - debt is meaningless for a bank/insurer (deposits & reserves are
        # operating liabilities), so never display it as Lynch net cash.
        nc = "n/m (financial)" if rec.get("is_financial") else m.get("net_cash_per_share")
        L.append("| {i} | {t} | {c} | {cat} | {g} | {pe} | {peg} | {da} | {nc} | {fl} | {ps} | {fs} |".format(
            i=i, t=rec.get("ticker", "?"), c=rec.get("company", "?"), cat=r["category"],
            g=m.get("growth_used_pct"), pe=m.get("pe"), peg=m.get("peg"),
            da=m.get("dividend_adjusted_peg"), nc=nc,
            fl=flags, ps=_prov(rec, "price"), fs=_prov(rec, "fund")))
    L += ["", "_P/E uses TTM EPS where available (FY fallback labeled). div-adj PEG uses latest "
          "declared DPS and may include specials - verify._", ""]

    L += ["## Manual review (NOT ranked - a cheap stock can be a trap)", "",
          "| Ticker | Company | Why set aside |", "|--------|---------|---------------|"]
    for r in result["manual"]:
        L.append(f"| {r['rec'].get('ticker','?')} | {r['rec'].get('company','?')} | {r['reason']} |")
    L += ["", "## Dropped (out of mechanical scope), by reason", ""]
    for reason, n in sorted(result["dropped_counts"].items(), key=lambda kv: -kv[1]):
        L.append(f"- {reason}: {n}")
    if not result["dropped_counts"]:
        L.append("- none")
    L += ["", "---", "*Candidates are leads, not buys. Next: `/screen` the top names, then "
          "`/research` 1-3 of them for a real (story + bear case + checklist) verdict.*", ""]
    return "\n".join(L)


def render_leads_rows(result, top_n, date_str):
    """leads.md rows for the top-N ranked candidates - explicitly labeled leads."""
    rows = []
    for r in result["ranked"][:top_n]:
        rec = r["rec"]
        name = f"{rec.get('ticker','?')} / {rec.get('company','?')}"
        rows.append(f"| {date_str} | {name} | from /scan {date_str} "
                    f"(PEG-ranked, unscreened - NOT a verdict) | lead |")
    return rows


# --------------------------------------------------------------------------- #
# Record acquisition: offline fixtures, or live EDGAR (frames + companyfacts)
# --------------------------------------------------------------------------- #
def load_fixture_records(fixtures_dir):
    """Each <TICKER>.json carries the resolved facts the engine needs (offline)."""
    records = []
    for path in sorted(glob.glob(os.path.join(fixtures_dir, "*.json"))):
        with open(path) as fh:
            records.append(json.load(fh))
    return records


def _period_days(item):
    try:
        s = datetime.date.fromisoformat(item["start"])
        e = datetime.date.fromisoformat(item["end"])
        return (e - s).days
    except (KeyError, ValueError, TypeError):
        return None


def ttm_eps_from_facts(facts):
    """Chain the 4 most recent CONSECUTIVE ~quarterly diluted-EPS facts -> TTM.
    Consecutive means each quarter starts within days of the previous one's end,
    so the four tile one trailing year. Without that check, a seasonal filer
    whose only standalone quarterly facts are the SAME big quarter from four
    different years (H&R Block's tax season) sums to a fantasy EPS (the HRB
    P/E-1.82 artifact). Returns (eps, source_label, as_of) or (None, None, None)
    if a full consecutive year isn't available (caller falls back to FY EPS)."""
    usgaap = facts.get("facts", {}).get("us-gaap", {})
    for tag in fe.CONCEPTS["eps"]:
        units = usgaap.get(tag, {}).get("units", {})
        items = units.get("USD/shares")
        if not items:
            continue
        quarters = {}
        for it in items:
            d = _period_days(it)
            if d is not None and 80 <= d <= 100 and it.get("end"):
                quarters[it["end"]] = (it["val"], it["start"])   # latest filing wins
        end, vals = max(quarters, default=None), []
        while end is not None and len(vals) < 4:
            val, start = quarters[end]
            vals.append(val)
            s = datetime.date.fromisoformat(start)
            end = next((e for e in quarters
                        if 0 <= (s - datetime.date.fromisoformat(e)).days <= 6), None)
        if len(vals) == 4:
            return round(sum(vals), 2), f"SEC EDGAR ({tag}, TTM=4q)", max(quarters)
    return None, None, None


def per_share_check(eps_series, ni_series, shares):
    """Cross-check the per-share basis: latest common FY's net income / current
    shares should land near that FY's reported EPS. A gap outside PER_SHARE_BAND
    means the share count doesn't match the EPS denominator (a dual-class issuer
    whose listed line is one class - the CHTR case - or a large noncontrolling
    interest), so PEG/net-cash-per-share built on it would be fiction. Returns a
    human-readable reason, or None when consistent / not computable."""
    if not eps_series or not ni_series or not shares:
        return None
    common = set(eps_series) & set(ni_series)
    if not common:
        return None
    yr = max(common)
    reported = eps_series[yr]
    if not isinstance(reported, (int, float)) or reported <= 0:
        return None
    implied = ni_series[yr] / shares
    lo, hi = PER_SHARE_BAND
    if not (lo <= implied / reported <= hi):
        return f"NI/shares implies EPS ~{implied:.2f} vs reported {reported} (FY{yr})"
    return None


def build_record_from_cik(cik, ticker, company, ua, years, n_classes=1):
    """Stage B: pull one survivor's exact companyfacts and assemble a record."""
    facts = fe.cached_json(fe.FACTS_URL.format(cik=cik), ua, f"facts_{cik}.json")
    src = f"SEC EDGAR companyfacts CIK{cik:010d}"
    eps_tag, _, eps_series = fe.annual_series(facts, fe.CONCEPTS["eps"], "USD/shares")
    eps_series = dict(sorted(eps_series.items())[-years:])
    _, dps_unit, dps_series = fe.annual_series(facts, fe.CONCEPTS["dividend_per_share"], "USD/shares")
    _, cash_val, cash_end = fe.latest(facts, fe.CONCEPTS["cash"], "USD")
    _, ltd_val, ltd_end = fe.latest(facts, fe.CONCEPTS["long_term_debt"], "USD")
    _, cur_val, _ = fe.latest(facts, fe.CONCEPTS["current_debt"], "USD")
    _, sh_val, _ = fe.latest(facts, fe.CONCEPTS["shares"], "shares")
    # NI-available-to-common first: it shares the EPS numerator's basis, so the
    # consistency check below doesn't false-alarm on preferred dividends / NCI.
    _, _, ni_series = fe.annual_series(
        facts, ["NetIncomeLossAvailableToCommonStockholdersBasic", "NetIncomeLoss"], "USD")

    ttm, ttm_src, ttm_end = ttm_eps_from_facts(facts)
    if ttm is None and eps_series:                          # FY fallback, labeled
        last_y = max(eps_series)
        ttm, ttm_src, ttm_end = eps_series[last_y], f"SEC EDGAR ({eps_tag}, FY{last_y} - TTM unavailable)", f"FY{last_y}"

    total_debt = None
    if ltd_val is not None or cur_val is not None:
        total_debt = (ltd_val or 0) + (cur_val or 0)

    usgaap = facts.get("facts", {}).get("us-gaap", {})
    return {
        "ticker": ticker, "company": company, "cik": cik,
        "eps_history": {str(k): v for k, v in eps_series.items()},
        "eps_ttm": ttm,
        "dividend_per_share": (sorted(dps_series.items())[-1][1] if dps_series else 0),
        "shares_outstanding": sh_val,
        "total_debt": total_debt,
        "cash": cash_val,
        "long_term_growth_estimate_pct": None,
        "n_share_classes": n_classes,
        "per_share_check": per_share_check(eps_series, ni_series, sh_val),
        "is_financial": any(t in usgaap for t in FINANCIAL_TAGS),
        "fund_source": ttm_src or src, "fund_as_of": ttm_end or cash_end or ltd_end,
        "price": None, "price_source": None, "price_as_of": None,
    }


def _ticker_rank(ticker, title=""):
    """Lower is more 'common-stock-like'. A CIK can list several tickers; we keep
    the common line. Priority: (1) no punctuation - a hyphen ("WRB-PH") or dot
    marks a preferred/class/warrant line whose ~$25-par price must never be paired
    with common-share EPS; (2) the ticker matching the company name's first token
    - a utility/bank common usually does and its SAME-LENGTH baby bonds do not
    (e.g. "DTE" for "DTE ENERGY CO" vs the bond tickers DTB/DTG/DTW, which would
    otherwise win the tie alphabetically); (3) shorter symbol (the common, not a
    suffixed note like "TMUSL"/"SOJD"); (4) alphabetical. Smallest key wins."""
    has_punct = any(c in ticker for c in "-.")
    first_tok = title.split()[0].upper() if title else ""
    name_match = 0 if (first_tok and ticker.upper() == first_tok) else 1
    return (1 if has_punct else 0, name_match, len(ticker), ticker)


def _class_base(ticker):
    """BRK-A / BRK.B / HEI-A -> BRK / BRK / HEI: a punctuated single-letter
    suffix is a share-class line. Longer suffixes (WRB-PH preferreds) and
    unpunctuated notes (TMUSL, DTB) are NOT classes and map to themselves."""
    if len(ticker) > 2 and ticker[-2] in "-." and ticker[-1].isalpha():
        return ticker[:-2]
    return ticker


def n_share_classes_from_tickers(tickers):
    """Count the largest group of one CIK's tickers that collapse to the same
    base after stripping a class suffix: BRK-A+BRK-B -> 2, HEI+HEI-A -> 2,
    WRB+WRB-PH -> 1, DTE+DTB+DTG -> 1. >1 means the issuer trades multiple
    share classes, so per-share math on any single line is unreliable (gate ->
    manual). Unpunctuated dual listings (GOOG/GOOGL) are NOT caught here - the
    per_share_check consistency gate is the second layer for those."""
    groups = {}
    for tk in tickers:
        groups[_class_base(tk)] = groups.get(_class_base(tk), 0) + 1
    return max(groups.values(), default=1)


def share_classes_by_cik(tmap):
    """{cik: n_share_classes} from the SEC ticker map (one CIK, many tickers)."""
    by_cik = {}
    for r in tmap.values():
        tk = r.get("ticker", "")
        if tk:
            by_cik.setdefault(int(r["cik_str"]), []).append(tk)
    return {cik: n_share_classes_from_tickers(tks) for cik, tks in by_cik.items()}


def stage_a_survivor_ciks(ua, years, end_year):
    """Stage A: pull diluted-EPS frames for the window, keep CIKs with enough
    positive annual points. Frames values are PROVISIONAL (a filter only)."""
    by_cik = {}
    for yr in range(end_year - years + 1, end_year + 1):
        try:
            frame = fe.cached_json(FRAMES_URL.format(concept="EarningsPerShareDiluted", year=yr),
                                   ua, f"frames_eps_{yr}.json")
        except Exception as e:             # broad on purpose (don't crash the sweep)
            print(f"# frames {yr} unavailable: {e}", file=sys.stderr)   # but never silent
            continue                       # a missing year just narrows the window
        for row in frame.get("data", []):
            by_cik.setdefault(row["cik"], {})[str(yr)] = row["val"]
    survivors = []
    for cik, series in by_cik.items():
        positive = [v for v in series.values() if isinstance(v, (int, float)) and v > 0]
        if len(positive) >= MIN_YEARS:     # provisional - re-checked exactly in Stage B
            survivors.append(cik)
    return survivors


def attach_prices(records, sleep):
    """Attach a yfinance price + REAL quote date to each record (screening-only).
    Missing/failed prices stay None -> screen_one drops them, counted.
    Emits '# prices: i/n' to stderr every 25 names so a long sweep is watchable
    (scripts/scan-watch renders these lines as a live progress bar)."""
    if yf is None:
        for r in records:
            r.setdefault("price", None)
        return records, "yfinance not installed"
    n = len(records)
    for i, rec in enumerate(records, 1):
        try:
            t = yf.Ticker(rec["ticker"])
            hist = t.history(period="5d")
            if len(hist):
                px = round(float(hist["Close"].iloc[-1]), 2)
                if px > 0:                      # reject non-positive / bad quotes
                    rec["price"] = px
                    rec["price_as_of"] = str(hist.index[-1].date())
                    rec["price_source"] = "yfinance (screening-only)"
        except Exception as e:                  # broad on purpose (one bad ticker
            # must not abort the whole sweep) - but log it, never swallow silently,
            # so a systematically-failing price source is visible, not invisible.
            print(f"# price skip {rec.get('ticker', '?')}: {e}", file=sys.stderr)
            rec["price"] = rec.get("price")     # leave None on failure (-> dropped, counted)
        if i % 25 == 0 or i == n:
            print(f"# prices: {i}/{n}", file=sys.stderr, flush=True)
        if sleep:
            time.sleep(sleep)
    return records, None


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Market-wide Lynch candidate screen (the funnel).")
    ap.add_argument("--tickers", help="comma-separated subset (skips Stage A frames)")
    ap.add_argument("--fixtures", help="dir of <TICKER>.json records - offline, no network")
    ap.add_argument("--years", type=int, default=5, help="EPS history window (default 5)")
    ap.add_argument("--top-n", type=int, default=40, help="rows appended to leads.md (default 40)")
    ap.add_argument("--sleep", type=float, default=0.15, help="seconds between live calls (rate-limit)")
    ap.add_argument("--no-price", action="store_true", help="Stage A quality only; skip price")
    ap.add_argument("--date", default=None, help="as-of date for output (default today)")
    ap.add_argument("--results", default=None,
                    help="output path for the ranked table (default scans/scan-results.md; a "
                         "--fixtures run defaults to scans/scan-results.fixtures.md so "
                         "verification never clobbers the real sweep output)")
    ap.add_argument("--leads", default="leads.md", help="leads.md to append top-N to")
    ap.add_argument("--write-leads", action="store_true", help="append top-N to --leads")
    ap.add_argument("--ua", default=os.environ.get("SEC_EDGAR_USER_AGENT",
                    "Up the Wall Street research-agent (set-your-contact@example.com)"))
    args = ap.parse_args()
    date_str = args.date or datetime.date.today().isoformat()

    # 1) acquire records
    if args.fixtures:
        records = load_fixture_records(args.fixtures)
    elif args.tickers:
        records = []
        classes = share_classes_by_cik(fe.cached_json(fe.TICKERS_URL, args.ua, "company_tickers.json"))
        for tk in [t.strip().upper() for t in args.tickers.split(",") if t.strip()]:
            try:
                cik, title = fe.ticker_to_cik(tk, args.ua)
                records.append(build_record_from_cik(cik, tk, title, args.ua, args.years,
                                                     n_classes=classes.get(cik, 1)))
                time.sleep(args.sleep)
            except Exception as e:
                print(f"# skip {tk}: {e}", file=sys.stderr)
    else:
        end_year = (int(args.date[:4]) if args.date else datetime.date.today().year) - 1
        survivors = stage_a_survivor_ciks(args.ua, args.years, end_year)
        print(f"# Stage A: {len(survivors)} survivors from frames", file=sys.stderr)
        tmap = fe.cached_json(fe.TICKERS_URL, args.ua, "company_tickers.json")
        # One CIK can list several tickers (common + preferred/class/notes).
        # Keep the COMMON-stock line: pairing a preferred's ~$25-par price with
        # common-share EPS fabricates a tiny P/E. _ticker_rank prefers it.
        cik_to_tt = {}
        for r in tmap.values():
            tk, title = r.get("ticker", ""), r.get("title", "")
            if not tk:
                continue
            cik = int(r["cik_str"])
            prev = cik_to_tt.get(cik)
            if prev is None or _ticker_rank(tk, title) < _ticker_rank(prev[0], prev[1]):
                cik_to_tt[cik] = (tk, title)
        classes = share_classes_by_cik(tmap)
        records = []
        for i, cik in enumerate(survivors, 1):
            tk, title = cik_to_tt.get(cik, ("", ""))
            if not tk:
                continue
            try:
                records.append(build_record_from_cik(cik, tk, title, args.ua, args.years,
                                                     n_classes=classes.get(cik, 1)))
                time.sleep(args.sleep)
            except Exception as e:
                print(f"# skip CIK{cik}: {e}", file=sys.stderr)
            if i % 100 == 0 or i == len(survivors):
                print(f"# fundamentals: {i}/{len(survivors)}", file=sys.stderr, flush=True)

    # 2) prices (screening-only) unless --no-price. --fixtures is OFFLINE by
    #    contract (docstring): fixtures carry their own price, so never hit the
    #    network for them - a live call would silently clobber the fixture price.
    if not args.no_price and not args.fixtures:
        attach_prices(records, args.sleep)

    # 3) screen + render
    result = screen_records(records, args.years)
    md = render_scan_results(result, date_str)
    # A --fixtures (verification) run must never overwrite the real sweep's
    # scans/scan-results.md; give it its own default unless the caller named a path.
    results_path = args.results or os.path.join(
        "scans", "scan-results.fixtures.md" if args.fixtures else "scan-results.md")
    parent = os.path.dirname(results_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(results_path, "w") as fh:
        fh.write(md)
    print(md)

    if args.write_leads:
        rows = render_leads_rows(result, args.top_n, date_str)
        if rows and os.path.exists(args.leads):
            lines = open(args.leads).read().splitlines()
            # insert right after the last existing table row so the new leads stay
            # contiguous with the table (not orphaned below the trailing comment).
            last_row = max((i for i, ln in enumerate(lines) if ln.lstrip().startswith("|")),
                           default=len(lines) - 1)
            lines[last_row + 1:last_row + 1] = rows
            with open(args.leads, "w") as fh:
                fh.write("\n".join(lines) + "\n")
            print(f"\n# inserted {len(rows)} leads into {args.leads}", file=sys.stderr)


if __name__ == "__main__":
    main()
