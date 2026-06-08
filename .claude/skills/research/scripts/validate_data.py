#!/usr/bin/env python3
"""validate_data.py - gate company data JSON before a verdict is written.

Enforces the anti-hallucination contract from playbook/03-numbers.md:
  - price and EPS must be present,
  - every present numeric OR qualitative input must be sourced (field-level
    provenance OR a top-level source), and
  - an as_of date must be present and parseable,
  - the Lynch category, if given, must be a real one.

Validate one file (legacy single JSON-object output, machine-readable) or many
(bulk gate - one OK/FAIL line per file, exit 1 if ANY file fails):

    python3 validate_data.py data.json
    python3 validate_data.py research/*.data.json   # bulk gate (scripts/verify)
    python3 validate_data.py -                       # read stdin

Exit 0 = all clean (warnings allowed). Exit 1 = at least one file has errors.
It must FAIL CLOSED: missing required fields or unsourced values are errors.
"""
import argparse
import datetime
import json
import sys

SCALE = ("_thousands", "_millions", "_billions")
# numeric inputs that must be sourced when present
NUMERIC_FIELDS = ["price", "eps_ttm", "dividend_per_share", "shares_outstanding",
                  "total_debt", "cash", "long_term_growth_estimate_pct",
                  "institutional_ownership_pct"]
# prose inputs (insider read, buyback posture) - not numbers, but still claims
# that must carry provenance so they can't be quietly invented.
QUALITATIVE_FIELDS = ["insider_activity", "buybacks"]
REQUIRED = ["price", "eps_ttm"]
RECOMMENDED = ["eps_history", "shares_outstanding", "total_debt", "cash",
               "dividend_per_share", "long_term_growth_estimate_pct",
               "institutional_ownership_pct"]
# The six Lynch categories + "Avoid". A parenthetical qualifier is allowed
# (e.g. "Fast grower (unprofitable / negative EPS)") - we match the base.
CATEGORIES = {"Slow grower", "Stalwart", "Fast grower", "Cyclical",
              "Asset play", "Turnaround", "Avoid"}


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


def has_reason(v):
    """An explicit gap is acceptable if it says why (a reason or at least a source)."""
    return isinstance(v, dict) and bool(v.get("reason") or v.get("source"))


def category_ok(category):
    """True if the category's base (before any '(...)') is a real Lynch category."""
    base = str(category).split("(")[0].strip()
    return base in CATEGORIES


def validate_doc(doc, max_age_days=400, today=None):
    """Pure check over one parsed document. Returns {ok, errors, warnings}.
    No I/O, so it is unit-testable and reused by the bulk path."""
    today = today or datetime.date.today()
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

    # Lynch category: valid enum if present, else recommend
    category = doc.get("category") or data.get("category")
    if category is None:
        warnings.append("missing recommended field: category (Lynch classification)")
    elif not category_ok(category):
        errors.append(f"category '{category}' is not a Lynch category {sorted(CATEGORIES)}")

    # required fields present (a null value counts as missing)
    for f in REQUIRED:
        k, v = resolve_key(data, f)
        if k is None or not is_present(v):
            errors.append(f"missing required field (no value yet): {f}")

    # provenance for every numeric/qualitative field that carries a value.
    # An explicit null must still say why (reason/source) - otherwise warn so the
    # gap is deliberate, never a silent omission.
    for f in NUMERIC_FIELDS + QUALITATIVE_FIELDS:
        k, v = resolve_key(data, f)
        if k is None:
            continue
        if not is_present(v):
            if isinstance(v, dict) and not has_reason(v):
                warnings.append(f"field '{k}' is null without a 'reason'/'source' - make the gap explicit")
            continue
        if not (has_field_provenance(v) or has_top_prov):
            errors.append(
                f"field '{k}' has no source/as_of - add field-level provenance "
                "or a top-level source+as_of")

    # recommended fields present. An explicit null WITH a documented reason
    # (e.g. a cyclical's n/m forward growth) is deliberate, not "missing" - don't
    # nag the disciplined "documented gap" pattern; only flag a true omission.
    for f in RECOMMENDED:
        k, v = resolve_key(data, f)
        if k is None or (not is_present(v) and not has_reason(v)):
            warnings.append(f"missing recommended field: {f} (needed for full valuation / net cash)")

    # staleness
    if parsed_as_of:
        age = (today - parsed_as_of).days
        if age > max_age_days:
            warnings.append(f"data is ~{age} days old (> {max_age_days}); refresh before relying on it")
        if age < 0:
            warnings.append("as_of is in the future")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def validate_file(path, max_age_days=400):
    """Read + validate a JSON file. Returns validate_doc()'s dict plus 'path'.
    A read/parse failure is itself an error (ok=False) - never a crash."""
    try:
        with open(path) as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as e:        # ValueError covers JSONDecodeError
        return {"ok": False, "errors": [f"cannot read/parse: {e}"], "warnings": [], "path": path}
    res = validate_doc(doc, max_age_days=max_age_days)
    res["path"] = path
    return res


def _validate_stdin(max_age_days):
    try:
        doc = json.loads(sys.stdin.read())
    except ValueError as e:
        return {"ok": False, "errors": [f"cannot parse stdin: {e}"], "warnings": []}
    return validate_doc(doc, max_age_days=max_age_days)


def main():
    ap = argparse.ArgumentParser(description="Validate company data before a verdict.")
    ap.add_argument("data", nargs="*", default=["-"],
                    help="path(s) to data JSON; omit or '-' to read stdin")
    ap.add_argument("--max-age-days", type=int, default=400,
                    help="warn if data is older than this (default 400)")
    args = ap.parse_args()
    paths = args.data or ["-"]

    # Single file / stdin keeps the legacy single JSON-object output so existing
    # callers that parse stdout (and the failing-closed contract) keep working.
    if len(paths) == 1:
        p = paths[0]
        res = _validate_stdin(args.max_age_days) if p == "-" else validate_file(p, args.max_age_days)
        print(json.dumps({"ok": res["ok"], "errors": res["errors"], "warnings": res["warnings"]}, indent=2))
        sys.exit(0 if res["ok"] else 1)

    # Bulk: per-file summary + aggregate; exit 1 if any file has errors.
    any_fail = False
    for p in paths:
        res = validate_file(p, args.max_age_days)
        any_fail = any_fail or not res["ok"]
        print(f"{'OK  ' if res['ok'] else 'FAIL'}  {p}  "
              f"(errors: {len(res['errors'])}, warnings: {len(res['warnings'])})")
        for e in res["errors"]:
            print(f"        ERROR: {e}")
        for w in res["warnings"]:
            print(f"        warn:  {w}")
    print(f"\n{'FAIL' if any_fail else 'OK'}: {len(paths)} file(s) checked")
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
