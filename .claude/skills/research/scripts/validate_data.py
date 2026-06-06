#!/usr/bin/env python3
"""validate_data.py - gate a company data JSON before a verdict is written.

Enforces the anti-hallucination contract from playbook/03-numbers.md:
  - price and EPS must be present,
  - every present numeric input must be sourced (field-level provenance OR a
    top-level source), and
  - an as_of date must be present and parseable.

Exit 0 = OK (warnings allowed). Exit 1 = errors (do not write a verdict).

Usage:
    python3 validate_data.py data.json
    python3 validate_data.py -            # read stdin
"""
import argparse
import datetime
import json
import sys

SCALE = ("_thousands", "_millions", "_billions")
NUMERIC_FIELDS = ["price", "eps_ttm", "dividend_per_share", "shares_outstanding",
                  "total_debt", "cash", "long_term_growth_estimate_pct",
                  "institutional_ownership_pct"]
REQUIRED = ["price", "eps_ttm"]
RECOMMENDED = ["eps_history", "shares_outstanding", "total_debt", "cash"]


def resolve_key(data, name):
    if name in data:
        return name, data[name]
    for s in SCALE:
        if name + s in data:
            return name + s, data[name + s]
    return None, None


def unwrap(v):
    return v["value"] if isinstance(v, dict) and "value" in v else v


def is_present(v):
    """A field counts as present only if it actually carries a (non-null) value."""
    return unwrap(v) is not None


def has_field_provenance(v):
    return isinstance(v, dict) and bool(v.get("source")) and bool(v.get("as_of"))


def main():
    ap = argparse.ArgumentParser(description="Validate company data before a verdict.")
    ap.add_argument("data", nargs="?", default="-",
                    help="path to data JSON; omit or '-' to read stdin")
    ap.add_argument("--max-age-days", type=int, default=400,
                    help="warn if data is older than this (default 400)")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.data == "-" else open(args.data).read()
    doc = json.loads(raw)
    # fetch_edgar.py nests fields under `inputs`; eval fixtures use `given_facts`.
    data = doc.get("given_facts") or doc.get("inputs") or doc

    errors, warnings = [], []
    top_source = doc.get("source") or data.get("source")
    top_as_of = doc.get("as_of") or data.get("as_of")
    has_top_prov = bool(top_source) and bool(top_as_of)

    # as_of present + parseable
    parsed_as_of = None
    if not top_as_of:
        warnings.append("no top-level 'as_of'; ensure every figure carries its own as_of")
    else:
        try:
            parsed_as_of = datetime.date.fromisoformat(str(top_as_of))
        except ValueError:
            errors.append(f"as_of '{top_as_of}' is not an ISO date (YYYY-MM-DD)")

    # required fields present (a null value counts as missing)
    for f in REQUIRED:
        k, v = resolve_key(data, f)
        if k is None or not is_present(v):
            errors.append(f"missing required field (no value yet): {f}")

    # provenance for every numeric field that actually carries a value
    for f in NUMERIC_FIELDS:
        k, v = resolve_key(data, f)
        if k is None or not is_present(v):
            continue
        if not (has_field_provenance(v) or has_top_prov):
            errors.append(
                f"field '{k}' has no source/as_of - add field-level provenance "
                "or a top-level source+as_of")

    # recommended fields present
    for f in RECOMMENDED:
        k, v = resolve_key(data, f)
        if k is None or not is_present(v):
            warnings.append(f"missing recommended field: {f} (needed for full valuation / net cash)")

    # staleness
    if parsed_as_of:
        age = (datetime.date.today() - parsed_as_of).days
        if age > args.max_age_days:
            warnings.append(f"data is ~{age} days old (> {args.max_age_days}); refresh before relying on it")
        if age < 0:
            warnings.append("as_of is in the future")

    result = {"ok": not errors, "errors": errors, "warnings": warnings}
    print(json.dumps(result, indent=2))
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
