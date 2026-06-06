#!/usr/bin/env python3
"""fetch_edgar.py - pull exact fundamentals from the free SEC EDGAR API.

Maps a ticker to its CIK, downloads the company's XBRL "facts", and assembles a
data.json scaffold (with per-field provenance) for the Lynch pipeline. This is
the deterministic, no-key fundamentals path (playbook/03). It does NOT provide a
market price (EDGAR has none) - leave `price` to web search or manual entry.

Network-dependent. On any failure it prints a JSON error and exits 2, so the
agent knows to fall back to web search, then to asking the user.

Usage:
    python3 fetch_edgar.py AAPL
    python3 fetch_edgar.py AAPL --years 5 --ua "Your Name you@example.com"

SEC requires a descriptive User-Agent with contact info. Set --ua or the
SEC_EDGAR_USER_AGENT env var.
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
CACHE_DIR = ".edgar_cache"

# us-gaap concept tags we try, in priority order, per logical field.
CONCEPTS = {
    "eps": ["EarningsPerShareDiluted", "EarningsPerShareBasic"],
    "dividend_per_share": ["CommonStockDividendsPerShareDeclared",
                           "CommonStockDividendsPerShareCashPaid"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue",
             "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
    "long_term_debt": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "current_debt": ["LongTermDebtCurrent", "DebtCurrent"],
    "shares": ["CommonStockSharesOutstanding"],
}


def http_json(url, ua):
    req = urllib.request.Request(url, headers={"User-Agent": ua,
                                               "Accept-Encoding": "gzip, deflate",
                                               "Host": url.split("/")[2]})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            import gzip
            data = gzip.decompress(data)
    return json.loads(data)


def cached_json(url, ua, cache_name):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, cache_name)
    if os.path.exists(path):
        try:
            return json.load(open(path))
        except (ValueError, OSError):
            pass
    obj = http_json(url, ua)
    try:
        json.dump(obj, open(path, "w"))
    except OSError:
        pass
    return obj


def ticker_to_cik(ticker, ua):
    table = cached_json(TICKERS_URL, ua, "company_tickers.json")
    ticker = ticker.upper()
    for row in table.values():
        if row.get("ticker", "").upper() == ticker:
            return int(row["cik_str"]), row.get("title", "")
    raise LookupError(f"ticker {ticker} not found in SEC EDGAR ticker map")


def annual_series(facts, tags, unit_hint=None):
    """Return {fiscal_year: value} from the first matching us-gaap tag, using
    annual (FY / 10-K) data points. Picks the largest-USD unit available."""
    usgaap = facts.get("facts", {}).get("us-gaap", {})
    for tag in tags:
        if tag not in usgaap:
            continue
        units = usgaap[tag].get("units", {})
        unit_key = unit_hint if unit_hint in units else next(iter(units), None)
        if not unit_key:
            continue
        series = {}
        for item in units[unit_key]:
            if item.get("form", "").startswith("10-K") and item.get("fp") == "FY" and item.get("fy"):
                series[int(item["fy"])] = item["val"]
        if series:
            return tag, unit_key, series
    return None, None, {}


def latest(facts, tags, unit_hint=None):
    """Most recent reported value (any form) for a balance-sheet style tag."""
    usgaap = facts.get("facts", {}).get("us-gaap", {})
    for tag in tags:
        if tag not in usgaap:
            continue
        units = usgaap[tag].get("units", {})
        unit_key = unit_hint if unit_hint in units else next(iter(units), None)
        if not unit_key:
            continue
        items = [i for i in units[unit_key] if i.get("end")]
        if items:
            best = max(items, key=lambda i: i["end"])
            return tag, best["val"], best["end"]
    return None, None, None


def prov(source, as_of):
    return {"source": source, "as_of": as_of}


def main():
    ap = argparse.ArgumentParser(description="Fetch fundamentals from SEC EDGAR.")
    ap.add_argument("ticker")
    ap.add_argument("--years", type=int, default=5, help="years of EPS history (default 5)")
    ap.add_argument("--ua", default=os.environ.get("SEC_EDGAR_USER_AGENT",
                    "Up the Wall Street research-agent (set-your-contact@example.com)"))
    args = ap.parse_args()

    try:
        cik, title = ticker_to_cik(args.ticker, args.ua)
        facts = cached_json(FACTS_URL.format(cik=cik), args.ua, f"facts_{cik}.json")
    except (urllib.error.URLError, urllib.error.HTTPError, LookupError, ValueError) as e:
        print(json.dumps({
            "error": str(e),
            "hint": "EDGAR unreachable or ticker unknown. Fall back to web search, then ask the user to paste figures.",
        }, indent=2))
        sys.exit(2)

    src = f"SEC EDGAR companyfacts CIK{cik:010d}"

    eps_tag, _, eps_series = annual_series(facts, CONCEPTS["eps"], "USD/shares")
    eps_series = dict(sorted(eps_series.items())[-args.years:])
    dps_tag, _, dps_series = annual_series(facts, CONCEPTS["dividend_per_share"], "USD/shares")
    cash_tag, cash_val, cash_end = latest(facts, CONCEPTS["cash"], "USD")
    ltd_tag, ltd_val, ltd_end = latest(facts, CONCEPTS["long_term_debt"], "USD")
    cur_tag, cur_val, cur_end = latest(facts, CONCEPTS["current_debt"], "USD")
    sh_tag, sh_val, sh_end = latest(facts, CONCEPTS["shares"], "shares")

    total_debt = None
    if ltd_val is not None or cur_val is not None:
        total_debt = (ltd_val or 0) + (cur_val or 0)

    latest_eps_year = max(eps_series) if eps_series else None

    out = {
        "ticker": args.ticker.upper(),
        "company": title,
        "cik": cik,
        "source": src,
        "as_of": cash_end or ltd_end or sh_end,
        "_note": "Fundamentals from SEC EDGAR (annual / 10-K). 'price' is NOT in EDGAR - fill via web search or manual entry. 'eps_ttm' here is the latest fiscal-year EPS; replace with trailing-twelve-month if you have it. Verify total_debt (XBRL debt tags vary).",
        "inputs": {
            "price": {"value": None, **prov("web search or manual - EDGAR has no price", None)},
            "eps_ttm": {"value": eps_series.get(latest_eps_year) if latest_eps_year else None,
                        **prov(f"{src} ({eps_tag}, FY{latest_eps_year})", f"FY{latest_eps_year}")},
            "eps_history": {"value": {str(k): v for k, v in eps_series.items()},
                            **prov(f"{src} ({eps_tag}, annual)", "FY series")},
            "dividend_per_share": {"value": (sorted(dps_series.items())[-1][1] if dps_series else 0),
                                   **prov(f"{src} ({dps_tag})" if dps_tag else "none found - assume 0", "latest FY")},
            "shares_outstanding": {"value": sh_val, **prov(f"{src} ({sh_tag})", sh_end)},
            "total_debt": {"value": total_debt,
                           **prov(f"{src} ({ltd_tag}+{cur_tag})" if total_debt is not None else "not found - verify manually", ltd_end or cur_end)},
            "cash": {"value": cash_val, **prov(f"{src} ({cash_tag})", cash_end)},
            "long_term_growth_estimate_pct": {"value": None,
                                              **prov("analyst estimate or your own - a forward guess; favor proven growth", None)},
            "institutional_ownership_pct": {"value": None, **prov("web search (e.g. 13F aggregates)", None)},
            "insider_activity": {"value": None, **prov("SEC Form 4 / web search", None)},
        },
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
