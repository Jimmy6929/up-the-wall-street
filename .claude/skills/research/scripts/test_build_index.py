"""Tests for build_index.py - the generated research/INDEX.md filter view.

Pins the exact output format (golden test), the verdict grouping + sort order
(reviewed desc, ticker asc), the selection rule (sidecar OR type frontmatter;
ledgers skipped), the "Needs attention" path for broken frontmatter (never a
crash, never a silent drop), self-exclusion/idempotence, pipe escaping, and the
--check CLI contract (exit 1 on stale/missing, never writes).

    python3 -m unittest discover -s .claude/skills/research/scripts -p 'test_*.py'
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest

import build_index as b

SCRIPT = os.path.join(os.path.dirname(__file__), "build_index.py")


def note(ticker, company, verdict, category="Stalwart", peg="1.0",
         as_of="2026-01-01", reviewed="2026-01-02", typed=True):
    type_line = "type: research-note\n" if typed else ""
    return (f"---\ntitle: {ticker} — {company}\nticker: {ticker}\ncompany: {company}\n"
            f"{type_line}category: {category}\nverdict: {verdict}\npeg: {peg}\n"
            f"as_of: {as_of}\nreviewed: {reviewed}\ntags: [research]\n---\n\n"
            f"# {ticker} — {company}\n")


def write(d, name, text):
    with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
        fh.write(text)


GOLDEN = """\
<!-- GENERATED — do not edit by hand.
     Regenerate: python3 .claude/skills/research/scripts/build_index.py
     Freshness is enforced by scripts/verify (build_index.py --check). -->

# Research index

> [!note] GENERATED — do not edit by hand; regenerate with `python3 .claude/skills/research/scripts/build_index.py`.
> Built from the YAML frontmatter of the `research/<TICKER>.md` notes (one row per note).
> Names tracked only in `watchlist.md` with no research note yet (e.g. COST) do not appear here.

3 notes: 1 Buy candidate · 1 Watchlist · 1 Pass/Avoid

## Buy candidate (1)

| Ticker | Company | Category | PEG | As of | Reviewed |
|---|---|---|---|---|---|
| [AAA](AAA.md) | Alpha Co | Fast grower | 0.85 | 2026-01-01 | 2026-01-02 |

## Watchlist (1)

| Ticker | Company | Category | PEG | As of | Reviewed |
|---|---|---|---|---|---|
| [BBB](BBB.md) | Beta Inc | Stalwart | 2.06 (rich) | 2026-02-01 | 2026-02-03 |

## Pass/Avoid (1)

| Ticker | Company | Category | PEG | As of | Reviewed |
|---|---|---|---|---|---|
| [CCC](CCC.md) | Gamma Corp | Avoid (hype) | n/a | 2026-03-04 | 2026-03-04 |
"""


class TestGolden(unittest.TestCase):
    def test_full_output_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "AAA.md", note("AAA", "Alpha Co", "Buy candidate",
                                    category="Fast grower", peg="0.85", reviewed="2026-01-02"))
            write(d, "BBB.md", note("BBB", "Beta Inc", "Watchlist", peg="2.06 (rich)",
                                    as_of="2026-02-01", reviewed="2026-02-03"))
            write(d, "BBB.data.json", "{}")
            write(d, "CCC.md", note("CCC", "Gamma Corp", "Pass/Avoid",
                                    category="Avoid (hype)", peg="n/a",
                                    as_of="2026-03-04", reviewed="2026-03-04"))
            write(d, "lessons.md", "- 2026-01-01 · AAA · a ledger line, not a note\n")
            content, n = b.build(d)
        self.assertEqual(content, GOLDEN)
        self.assertEqual(n, 3)


class TestSelection(unittest.TestCase):
    def test_ledger_without_sidecar_or_type_is_skipped_silently(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "alerts.md", "- 2026-06-11 · BR · valuation-threshold fired\n")
            content, n = b.build(d)
        self.assertEqual(n, 0)
        self.assertNotIn("alerts.md", content)
        self.assertNotIn("Needs attention", content)

    def test_sidecar_pairs_note_even_without_type(self):
        # The CSV regression: a real note (sidecar present) missing `type:` must
        # surface under Needs attention, not vanish from the index.
        with tempfile.TemporaryDirectory() as d:
            write(d, "XXX.md", note("XXX", "X Co", "Watchlist", typed=False))
            write(d, "XXX.data.json", "{}")
            content, n = b.build(d)
        self.assertEqual(n, 0)
        self.assertIn("## Needs attention (1)", content)
        self.assertIn("`XXX.md` — frontmatter missing `type: research-note`", content)
        self.assertNotIn("[XXX](XXX.md)", content)


class TestSortOrder(unittest.TestCase):
    def test_reviewed_desc_then_ticker_asc(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "AAA.md", note("AAA", "A", "Watchlist", reviewed="2026-05-01"))
            write(d, "ZZZ.md", note("ZZZ", "Z", "Watchlist", reviewed="2026-06-01"))
            write(d, "MMM.md", note("MMM", "M", "Watchlist", reviewed="2026-06-01"))
            content, _ = b.build(d)
        order = [content.find(f"[{t}]") for t in ("MMM", "ZZZ", "AAA")]
        self.assertTrue(all(i >= 0 for i in order), content)
        self.assertEqual(order, sorted(order))     # MMM before ZZZ (tie), AAA last (older)


class TestNeedsAttention(unittest.TestCase):
    def test_broken_notes_are_listed_with_reasons_never_crash(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "NOF.md", "# no frontmatter at all\n")
            write(d, "NOF.data.json", "{}")
            write(d, "BADV.md", note("BADV", "B Co", "Hold"))
            write(d, "BADD.md", note("BADD", "D Co", "Watchlist", reviewed="June 2026"))
            content, n = b.build(d)
        self.assertEqual(n, 0)
        self.assertIn("## Needs attention (3)", content)
        self.assertIn("`NOF.md` — no YAML frontmatter block", content)
        self.assertIn("unrecognized verdict 'Hold'", content)
        self.assertIn("`reviewed: June 2026` is not YYYY-MM-DD", content)
        for t in ("NOF", "BADV", "BADD"):
            self.assertNotIn(f"[{t}](", content)   # broken notes never become rows

    def test_verdict_match_is_case_insensitive(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "LOW.md", note("LOW", "L Co", "watchlist"))
            content, n = b.build(d)
        self.assertEqual(n, 1)
        self.assertIn("[LOW](LOW.md)", content)


class TestIdempotence(unittest.TestCase):
    def test_index_excludes_itself_and_rebuild_is_identical(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "AAA.md", note("AAA", "A Co", "Watchlist"))
            first, _ = b.build(d)
            write(d, "INDEX.md", first)
            second, n = b.build(d)
        self.assertEqual(first, second)
        self.assertEqual(n, 1)


class TestPipeEscaping(unittest.TestCase):
    def test_pipe_in_cell_is_escaped_and_column_count_holds(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "PIP.md", note("PIP", "P Co", "Watchlist", category="AI | hype"))
            content, _ = b.build(d)
        row = next(ln for ln in content.splitlines() if "[PIP]" in ln)
        self.assertIn("AI \\| hype", row)
        self.assertEqual(len(re.findall(r"(?<!\\)\|", row)), 7)   # 6 cells = 7 real pipes


class TestCLI(unittest.TestCase):
    def _run(self, d, *args):
        return subprocess.run([sys.executable, SCRIPT, "--research-dir", d, *args],
                              capture_output=True, text=True)

    def test_check_missing_index_exits_1(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "AAA.md", note("AAA", "A Co", "Watchlist"))
            r = self._run(d, "--check")
            self.assertEqual(r.returncode, 1)
            self.assertIn("stale", r.stderr)
            self.assertFalse(os.path.exists(os.path.join(d, "INDEX.md")))   # --check never writes

    def test_write_then_check_is_current_then_stale_after_edit(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "AAA.md")
            write(d, "AAA.md", note("AAA", "A Co", "Watchlist", reviewed="2026-01-02"))
            r = self._run(d)
            self.assertEqual(r.returncode, 0)
            self.assertIn("wrote", r.stdout)
            self.assertEqual(self._run(d, "--check").returncode, 0)

            with open(os.path.join(d, "INDEX.md"), "rb") as fh:
                before = fh.read()
            with open(p) as fh:
                text = fh.read()
            write(d, "AAA.md", text.replace("reviewed: 2026-01-02", "reviewed: 2026-02-02"))
            r = self._run(d, "--check")
            self.assertEqual(r.returncode, 1)
            with open(os.path.join(d, "INDEX.md"), "rb") as fh:
                after = fh.read()
            self.assertEqual(before, after)        # --check never modifies the index


if __name__ == "__main__":
    unittest.main()
