#!/usr/bin/env python3
"""build_index.py - regenerate research/INDEX.md, the generated filter view.

research/ stays FLAT on purpose: a verdict change (a /recheck flipping
Watchlist -> Pass) must never move files, break links in watchlist.md/leads.md,
or churn git history. The browsing/filtering layer is this generated index
instead: notes grouped by verdict, built from the YAML frontmatter every note
already carries (templates/research-note.md).

A note is any research/<X>.md with an <X>.data.json sidecar beside it OR
declaring `type: research-note` in frontmatter. Ledger files (lessons.md,
alerts.md) have neither and are skipped. A note with broken or incomplete
frontmatter lands under "Needs attention" with a reason - never silently
dropped, never a crash.

The output is deterministic (no wall-clock timestamps), so --check can
byte-compare the committed INDEX.md against a fresh in-memory build.

Usage:
    python3 build_index.py            # regenerate research/INDEX.md in place
    python3 build_index.py --check    # exit 1 if INDEX.md is stale or missing; never writes
"""
import argparse
import datetime
import glob
import os
import sys

from check_research_markdown import frontmatter_range

VERDICTS = ("Buy candidate", "Watchlist", "Pass/Avoid")
REQUIRED = ("ticker", "company", "verdict", "reviewed")
REGEN_CMD = "python3 .claude/skills/research/scripts/build_index.py"


def parse_frontmatter(lines):
    """Flat `key: value` frontmatter -> dict, or None if there is no block."""
    fm = frontmatter_range(lines)
    if not fm:
        return None
    data = {}
    for i in sorted(fm)[1:-1]:
        if ":" not in lines[i]:
            continue
        key, value = lines[i].split(":", 1)
        data[key.strip()] = value.strip()
    return data


def classify_note(path):
    """Return ("row", dict) | ("attention", reason) | ("skip", None) for one .md file."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    meta = parse_frontmatter(lines)
    sidecar = os.path.exists(path[:-3] + ".data.json")
    declared = meta is not None and meta.get("type") == "research-note"
    if not sidecar and not declared:
        return ("skip", None)               # ledger (lessons.md, alerts.md) or stray file
    if meta is None:
        return ("attention", "no YAML frontmatter block")
    if "type" not in meta:
        return ("attention", "frontmatter missing `type: research-note`")
    if meta["type"] != "research-note":
        return ("attention", f"frontmatter `type: {meta['type']}` (expected `research-note`)")
    missing = [k for k in REQUIRED if not meta.get(k)]
    if missing:
        return ("attention", "frontmatter missing " + ", ".join(f"`{k}`" for k in missing))
    verdict = next((v for v in VERDICTS if v.lower() == meta["verdict"].lower()), None)
    if verdict is None:
        return ("attention", f"unrecognized verdict {meta['verdict']!r} "
                             f"(expected {' / '.join(VERDICTS)})")
    try:
        datetime.date.fromisoformat(meta["reviewed"])
    except ValueError:
        return ("attention", f"`reviewed: {meta['reviewed']}` is not YYYY-MM-DD")
    return ("row", {
        "file": os.path.basename(path),
        "ticker": meta["ticker"],
        "company": meta["company"],
        "category": meta.get("category", "?"),
        "peg": meta.get("peg", "?"),
        "as_of": meta.get("as_of", "?"),
        "reviewed": meta["reviewed"],
        "verdict": verdict,
    })


def _cell(value):
    """A frontmatter value rendered inside a markdown table cell."""
    return str(value).replace("|", "\\|")


def render(rows, attention):
    groups = {v: [] for v in VERDICTS}
    for r in rows:
        groups[r["verdict"]].append(r)
    for group in groups.values():
        group.sort(key=lambda r: r["ticker"])                  # tiebreak: ticker asc
        group.sort(key=lambda r: r["reviewed"], reverse=True)  # reviewed desc (stable)

    counts = " · ".join(f"{len(groups[v])} {v}" for v in VERDICTS)
    out = [
        "<!-- GENERATED — do not edit by hand.",
        f"     Regenerate: {REGEN_CMD}",
        "     Freshness is enforced by scripts/verify (build_index.py --check). -->",
        "",
        "# Research index",
        "",
        f"> [!note] GENERATED — do not edit by hand; regenerate with `{REGEN_CMD}`.",
        "> Built from the YAML frontmatter of the `research/<TICKER>.md` notes (one row per note).",
        "> Names tracked only in `watchlist.md` with no research note yet (e.g. COST) do not appear here.",
        "",
        f"{len(rows)} notes: {counts}",
    ]
    for verdict in VERDICTS:
        group = groups[verdict]
        out += ["", f"## {verdict} ({len(group)})", ""]
        if not group:
            out.append("_none_")
            continue
        out.append("| Ticker | Company | Category | PEG | As of | Reviewed |")
        out.append("|---|---|---|---|---|---|")
        for r in group:
            out.append("| [{ticker}]({file}) | {company} | {category} | {peg} "
                       "| {as_of} | {reviewed} |".format(**{k: _cell(v) for k, v in r.items()}))
    if attention:
        out += ["", f"## Needs attention ({len(attention)})", ""]
        for name, reason in sorted(attention):
            out.append(f"- `{name}` — {reason}")
    return "\n".join(out) + "\n"


def build(research_dir, index_name="INDEX.md"):
    """Return (rendered markdown, number of well-formed notes)."""
    rows, attention = [], []
    for path in sorted(glob.glob(os.path.join(research_dir, "*.md"))):
        if os.path.basename(path) == index_name:
            continue
        kind, payload = classify_note(path)
        if kind == "row":
            rows.append(payload)
        elif kind == "attention":
            attention.append((os.path.basename(path), payload))
    return render(rows, attention), len(rows)


def main():
    ap = argparse.ArgumentParser(description="Regenerate (or check) the research/INDEX.md filter view.")
    ap.add_argument("--research-dir", default=None,
                    help="notes directory (default: <repo>/research, derived from this file)")
    ap.add_argument("--out", default=None, help="index path (default: <research-dir>/INDEX.md)")
    ap.add_argument("--check", action="store_true",
                    help="compare the existing index against a fresh build; exit 1 if stale "
                         "or missing - never writes (used by scripts/verify)")
    args = ap.parse_args()

    repo = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "..", "..", "..", ".."))
    research_dir = args.research_dir or os.path.join(repo, "research")
    out = args.out or os.path.join(research_dir, "INDEX.md")
    content, n_notes = build(research_dir, index_name=os.path.basename(out))
    shown = os.path.relpath(out)

    if args.check:
        try:
            with open(out, encoding="utf-8") as fh:
                current = fh.read()
        except OSError:
            current = None
        if current == content:
            print(f"{shown} is current ({n_notes} notes)")
            return 0
        print(f"{shown} is stale (or missing) — regenerate:\n  {REGEN_CMD}", file=sys.stderr)
        return 1

    with open(out, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"wrote {shown} ({n_notes} notes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
