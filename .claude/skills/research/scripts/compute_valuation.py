#!/usr/bin/env python3
"""compute_valuation.py - deterministic valuation math for the Lynch method.

Reads a company data JSON (file path, or '-' for stdin) and prints computed
metrics as JSON. The model must NOT compute these by hand; run this script and
read its output (see playbook/03-numbers.md). Finance is where language models
hallucinate most convincingly, so the arithmetic lives here.

Field resolution is forgiving. A field may be given as:
    "price": 78.0
    "price": {"value": 78.0, "source": "...", "as_of": "..."}
    "shares_outstanding_millions": 4200      (unit suffix auto-scaled)
so the script runs directly on the eval fixtures' `given_facts` blocks.

Usage:
    python3 compute_valuation.py data.json
    python3 compute_valuation.py - --category Cyclical   # read stdin
"""
import argparse
import json
import sys

# Convenience unit suffixes -> multiplier to absolute units.
SCALE = {"_thousands": 1e3, "_millions": 1e6, "_billions": 1e9}

# Interpretation thresholds (documented, not magic). From ch.13/15.
PEG_ATTRACTIVE = 1.0     # PEG below this: paying less than the growth rate
PEG_FAIR_MAX = 1.2       # up to here: roughly fair
UNSUSTAINABLE_GROWTH = 50  # % growth at/above which Lynch says discount it (ch.15)
CROWDED_OWNERSHIP = 85   # % institutional ownership that signals "no room to discover"


def _unwrap(v):
    return v["value"] if isinstance(v, dict) and "value" in v else v


def get_value(data, name, *aliases, default=None):
    """Resolve a field by canonical name or alias, tolerating {value:...}
    wrappers and *_thousands/_millions/_billions suffixes (scaled to absolute)."""
    for key in (name, *aliases):
        if key in data:
            return _unwrap(data[key])
        for suffix, mult in SCALE.items():
            if key + suffix in data:
                val = _unwrap(data[key + suffix])
                return val * mult if isinstance(val, (int, float)) else val
    return default


def cagr_pct(history):
    """Compound annual growth rate (%) from {year: eps}. Returns None when not
    computable: needs >=2 points and positive endpoints (CAGR is undefined
    across a sign change)."""
    if not isinstance(history, dict) or len(history) < 2:
        return None
    try:
        pts = sorted((int(y), float(v)) for y, v in history.items())
    except (ValueError, TypeError):
        return None
    (y0, v0), (y1, v1) = pts[0], pts[-1]
    years = y1 - y0
    if years <= 0 or v0 <= 0 or v1 <= 0:
        return None
    return ((v1 / v0) ** (1 / years) - 1) * 100


def main():
    ap = argparse.ArgumentParser(description="Deterministic Lynch valuation math.")
    ap.add_argument("data", nargs="?", default="-",
                    help="path to data JSON; omit or '-' to read stdin")
    ap.add_argument("--category", default=None,
                    help="category override (e.g. Cyclical) for caveat flags")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.data == "-" else open(args.data).read()
    doc = json.loads(raw)
    # Resolve fields from a nested block: eval fixtures use `given_facts`,
    # fetch_edgar.py output uses `inputs`. Top-level keys win if neither exists.
    data = doc.get("given_facts") or doc.get("inputs") or doc

    category = (args.category or doc.get("category")
                or get_value(data, "category") or "").strip().lower()

    price = get_value(data, "price")
    eps_ttm = get_value(data, "eps_ttm")
    eps_history = get_value(data, "eps_history")
    dps = get_value(data, "dividend_per_share", default=0) or 0
    fwd_growth = get_value(data, "long_term_growth_estimate_pct")
    shares = get_value(data, "shares_outstanding")
    debt = get_value(data, "total_debt", default=0) or 0
    cash = get_value(data, "cash", default=0) or 0
    burn = get_value(data, "cash_burn_per_year", "cash_burn_millions_per_year_raw")
    if burn is None and "cash_burn_millions_per_year" in data:
        burn = _unwrap(data["cash_burn_millions_per_year"]) * 1e6

    out = {"flags": [], "notes": []}

    # --- P/E -------------------------------------------------------------
    pe = None
    if isinstance(price, (int, float)) and isinstance(eps_ttm, (int, float)):
        if eps_ttm > 0:
            pe = round(price / eps_ttm, 2)
        else:
            out["flags"].append("negative_or_zero_earnings")
            out["notes"].append(
                "EPS <= 0: P/E and PEG are not meaningful. There is no "
                "earnings-based valuation; any case rests on a binary/recovery/"
                "asset story (ch.13).")
    out["pe"] = pe

    # --- growth ----------------------------------------------------------
    hist = cagr_pct(eps_history)
    out["historical_growth_pct"] = None if hist is None else round(hist, 1)
    out["forward_growth_estimate_pct"] = fwd_growth
    growth = fwd_growth if isinstance(fwd_growth, (int, float)) else hist
    out["growth_used_pct"] = None if growth is None else round(growth, 1)
    if isinstance(growth, (int, float)) and growth >= UNSUSTAINABLE_GROWTH:
        out["flags"].append("unsustainable_growth")
        out["notes"].append(
            f"Growth >= {UNSUSTAINABLE_GROWTH}% is rarely sustainable; "
            "discount it (ch.15).")
    if (isinstance(hist, (int, float)) and isinstance(fwd_growth, (int, float))
            and hist > 2 * fwd_growth + 10):
        out["notes"].append(
            "Historical growth far exceeds the forward estimate - typical of a "
            "cyclical near a peak; do not extrapolate the recent rate.")

    # --- PEG -------------------------------------------------------------
    peg = None
    if pe is not None and isinstance(growth, (int, float)) and growth > 0:
        peg = round(pe / growth, 2)
    out["peg"] = peg

    # --- dividend yield + dividend-adjusted PEG --------------------------
    dy = None
    if isinstance(price, (int, float)) and price > 0 and isinstance(dps, (int, float)):
        dy = round(dps / price * 100, 2)
    out["dividend_yield_pct"] = dy
    dapeg = None
    if pe is not None and pe > 0 and isinstance(growth, (int, float)) and dy is not None:
        dapeg = round((growth + dy) / pe, 2)
    out["dividend_adjusted_peg"] = dapeg

    # --- balance sheet ---------------------------------------------------
    net_cash = cash - debt if isinstance(cash, (int, float)) and isinstance(debt, (int, float)) else None
    out["net_cash"] = net_cash
    out["net_cash_per_share"] = (
        round(net_cash / shares, 2)
        if net_cash is not None and isinstance(shares, (int, float)) and shares else None)
    if debt == 0:
        out["flags"].append("no_debt")
        out["notes"].append("No debt - 'a company with no debt can't go bankrupt' (ch.13).")

    # --- cash runway (pre-profit companies) ------------------------------
    if isinstance(burn, (int, float)) and burn > 0 and isinstance(cash, (int, float)):
        out["cash_runway_years"] = round(cash / burn, 1)
        out["notes"].append("Cash runway is a survival metric, not a thesis.")

    # --- PEG interpretation (non-cyclical only) --------------------------
    is_cyclical = category == "cyclical"
    if is_cyclical:
        out["flags"].append("cyclical_caveat")
        out["notes"].append(
            "CYCLICAL: a low P/E on peak earnings is a DANGER sign, not a "
            "bargain (ch.15). PEG is misleading here; judge by cycle position, "
            "capacity, and inventories.")
    elif peg is not None:
        if peg < PEG_ATTRACTIVE:
            out["flags"].append("peg_attractive")
            out["notes"].append("PEG < 1: attractive - paying less than the growth rate (ch.13).")
        elif peg <= PEG_FAIR_MAX:
            out["notes"].append("PEG ~1: roughly fairly priced.")
        else:
            out["flags"].append("peg_rich")
            out["notes"].append("PEG > ~1.2: rich - paying up for growth; beware (ch.13).")

    # --- numbers-adjacent screen helpers ---------------------------------
    inst = get_value(data, "institutional_ownership_pct")
    if isinstance(inst, (int, float)) and inst >= CROWDED_OWNERSHIP:
        out["flags"].append("crowded_ownership")
        out["notes"].append(
            f"Institutional ownership ~{inst}%: crowded, little room to be "
            "discovered (opposite of a Lynch setup).")
    insider = str(get_value(data, "insider_activity", "insider_buying", default="") or "").lower()
    if "sell" in insider:
        out["flags"].append("insider_selling")

    out["scale_reminder"] = {
        "peg": "~1 fair, ~0.5 great, ~2 overpriced",
        "dividend_adjusted_peg": "<1 poor, 1.5 ok, >=2 excellent",
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
