#!/usr/bin/env python3
"""check_research_markdown.py - make "every number gets a source + as-of" checkable.

Research notes source numbers by a *table-based deferred* convention, not inline
markers: figures appear bare in prose, and the provenance lives in the Section-4
metrics table (a `| Metric | Value | Source | As of |` table) and the `## Sources`
list. So a naive "is there a source marker next to this number?" check would be
all noise. This linter instead checks what actually holds the note together:

  FAIL (structural - a real regression if violated):
    - the Section-4 metrics table is present (header has Source AND As of/As-of),
    - no data row in it has a blank Source or As-of cell, and
    - a `## Sources` section exists.

  warn (advisory - high-recall, deliberately not blocking):
    - a financial number in prose that does NOT appear anywhere in the metrics
      table or Sources block, and isn't allowlisted (chapter/section refs,
      checklist #N, gate N, bare years/ISO dates, ~approximations, method
      thresholds like "PEG < 1"). Numbers are excluded from being "numbers" unless
      they carry $, %, x/x-multiple, or a decimal point, which already drops
      "ch. 06", "#13", "gate 10", and plain years.

Usage:
    python3 check_research_markdown.py research/*.md
    python3 check_research_markdown.py --warn-only research/*.md   # always exit 0

Exit 1 if any structural FAIL (unless --warn-only). warns never affect the exit
code - they print so a human can promote them to FAILs once the rule is proven.
"""
import argparse
import re
import sys

# A token counts as a "financial number" only if it carries $, %, a x-multiple,
# or a decimal point. That alone excludes chapter refs, #N, gate N, and bare
# years - they never reach the allowlist or membership test.
FINANCIAL_NUM = re.compile(r"""
      \$\s?\d[\d,]*(?:\.\d+)?\s?(?:[BMK]|bn|tn|billion|million|trillion)?  # $ amounts
    | \d+(?:\.\d+)?\s?%                                                    # percentages
    | \d+(?:\.\d+)?\s?[×x](?![a-zA-Z])                                     # multiples 1.9x / 4.0x
    | \d+\.\d+                                                             # bare decimals (PEG, P/E)
""", re.VERBOSE)

DASHES = "–—-"


def _cells(line):
    """Split a markdown table row into stripped cell strings."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _is_separator(cells):
    """A `|---|:--:|` style separator row, not data."""
    return bool(cells) and all(re.fullmatch(r":?-{1,}:?", c) for c in cells if c != "") \
        and any("-" in c for c in cells)


def frontmatter_range(lines):
    if not lines or lines[0].strip() != "---":
        return set()
    for j in range(1, len(lines)):
        if lines[j].strip() == "---":
            return set(range(0, j + 1))
    return set()


def find_metrics_table(lines):
    """First table whose header carries Source AND As of/As-of (== Section 4)."""
    asof_names = ("as of", "as-of", "asof")
    for i, ln in enumerate(lines):
        if not ln.lstrip().startswith("|"):
            continue
        header = [c.lower() for c in _cells(ln)]
        if "source" in header and any(c in asof_names for c in header):
            src = header.index("source")
            asof = next(j for j, c in enumerate(header) if c in asof_names)
            rows, j = [], i + 1
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rc = _cells(lines[j])
                if not _is_separator(rc):
                    rows.append((j, rc))
                j += 1
            return {"src": src, "asof": asof, "ncol": len(header),
                    "rows": rows, "span": set(range(i, j))}
    return None


def sources_range(lines):
    start = None
    for i, ln in enumerate(lines):
        if re.match(r"^\s*#{1,6}\s+sources\b", ln, re.I):
            start = i
            break
    if start is None:
        return set()
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r"^\s*#{1,6}\s+\S", lines[j]):
            end = j
            break
    return set(range(start, end))


def _core(token):
    """The numeric core of a token: '$2.92B' -> '2.92', '90%' -> '90'."""
    m = re.search(r"\d[\d,]*(?:\.\d+)?", token)
    return m.group().replace(",", "") if m else ""


def _allowlisted(line, m):
    """True if this prose number is a legitimately-unsourced kind: an
    approximation (~/≈), a method threshold (<,>,≤,≥ before it), or part of a
    numeric range a–b (guidance/method ranges)."""
    before = line[max(0, m.start() - 3):m.start()]
    after = line[m.end():m.end() + 2]
    if "~" in before or "≈" in before:
        return True
    b = before.rstrip()
    if b and b[-1] in "<>≤≥":
        return True
    if after[:1] in DASHES and after[1:2].isdigit():
        return True
    if before[-1:] in DASHES and before[-2:-1].isdigit():
        return True
    return False


def check_markdown(text):
    """Return {"fails": [(line, msg)], "warns": [(line, msg)]} for one note."""
    lines = text.splitlines()
    fails, warns = [], []

    fm = frontmatter_range(lines)
    table = find_metrics_table(lines)
    src_range = sources_range(lines)

    # --- structural FAILs ---
    if table is None:
        fails.append((1, "no Section-4 metrics table found (needs columns incl. 'Source' and 'As of')"))
    else:
        for idx, rc in table["rows"]:
            if len(rc) != table["ncol"]:
                continue                       # wrapped/odd row - don't false-FAIL
            if rc[table["src"]] == "":
                fails.append((idx + 1, "metrics-table row has a blank Source cell"))
            if rc[table["asof"]] == "":
                fails.append((idx + 1, "metrics-table row has a blank As-of cell"))
    if not src_range:
        fails.append((1, "no '## Sources' section found"))

    # --- advisory coverage warns ---
    table_span = table["span"] if table else set()
    sourced = " ".join(lines[i] for i in sorted(table_span | src_range)).replace(",", "")
    skip = fm | table_span | src_range
    for i, ln in enumerate(lines):
        if i in skip:
            continue
        for m in FINANCIAL_NUM.finditer(ln):
            if _allowlisted(ln, m):
                continue
            core = _core(m.group())
            if core and core in sourced:
                continue
            warns.append((i + 1, f"prose number {m.group().strip()!r} not found in metrics "
                                 "table / Sources (verify it's sourced)"))
    return {"fails": fails, "warns": warns}


def main():
    ap = argparse.ArgumentParser(description="Check research notes for sourced-number coverage.")
    ap.add_argument("files", nargs="+", help="markdown notes to check (e.g. research/*.md)")
    ap.add_argument("--warn-only", action="store_true",
                    help="print findings but always exit 0 (advisory mode, used by scripts/verify)")
    args = ap.parse_args()

    any_fail, total_fail, total_warn = False, 0, 0
    for p in args.files:
        try:
            text = open(p).read()
        except OSError as e:
            print(f"{p}:0  FAIL  cannot read: {e}")
            any_fail = True
            continue
        res = check_markdown(text)
        for ln, msg in res["fails"]:
            print(f"{p}:{ln}  FAIL  {msg}")
        for ln, msg in res["warns"]:
            print(f"{p}:{ln}  warn  {msg}")
        total_fail += len(res["fails"])
        total_warn += len(res["warns"])
        any_fail = any_fail or bool(res["fails"])

    print(f"\n{total_fail} structural failure(s), {total_warn} advisory warning(s) "
          f"across {len(args.files)} file(s)")
    sys.exit(0 if args.warn_only else (1 if any_fail else 0))


if __name__ == "__main__":
    main()
