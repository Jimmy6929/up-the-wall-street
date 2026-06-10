"""Tests for check_research_markdown.py - sourced-number coverage in notes.

Proves the STRUCTURAL gate (the part that blocks): a complete metrics table with
no blank Source/As-of cells + a Sources section. Proves the advisory WARN pass
doesn't fire on the legitimately-unsourced kinds (chapter refs, #N, years,
~approximations, method thresholds) but does fire on a genuinely uncited prose
number. Regression-pins that every real research/*.md is structurally complete.

    python3 -m unittest discover -s .claude/skills/research/scripts -p 'test_*.py'
"""
import glob
import os
import subprocess
import sys
import tempfile
import unittest

import check_research_markdown as c

REPO = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
RESEARCH = os.path.join(REPO, "research")
SCRIPT = os.path.join(os.path.dirname(__file__), "check_research_markdown.py")

GOOD = """\
---
title: X — Test Co
---
## 3. Screen
Per ch. 06, a lead (#13) from 2007 with ~2.0 PEG; threshold PEG < 1.0, ≥50% growth.

## 4. The numbers
| Metric | Value | Source | As of |
|---|---|---|---|
| Price | $10.00 | web quote | 2026-06-01 |
| P/E | 10.0 | computed | 2026-06-01 |
| Earnings growth | 8.0% | computed | — |

## Sources
- Price $10.00 — web quote, 2026-06-01
"""


def fails_msgs(text):
    return [m for _, m in c.check_markdown(text)["fails"]]


def warn_msgs(text):
    return [m for _, m in c.check_markdown(text)["warns"]]


class TestStructural(unittest.TestCase):
    def test_good_note_has_no_failures(self):
        self.assertEqual(c.check_markdown(GOOD)["fails"], [])

    def test_blank_source_cell_fails(self):
        bad = GOOD.replace("| Price | $10.00 | web quote | 2026-06-01 |",
                           "| Price | $10.00 |  | 2026-06-01 |")
        self.assertTrue(any("blank Source" in m for m in fails_msgs(bad)))

    def test_blank_asof_cell_fails(self):
        bad = GOOD.replace("| Price | $10.00 | web quote | 2026-06-01 |",
                           "| Price | $10.00 | web quote |  |")
        self.assertTrue(any("blank As-of" in m for m in fails_msgs(bad)))

    def test_missing_metrics_table_fails(self):
        no_table = "## 4. The numbers\nno table here\n\n## Sources\n- x\n"
        self.assertTrue(any("metrics table" in m for m in fails_msgs(no_table)))

    def test_missing_sources_section_fails(self):
        no_sources = GOOD.replace("## Sources\n- Price $10.00 — web quote, 2026-06-01\n", "")
        self.assertTrue(any("Sources" in m for m in fails_msgs(no_sources)))


class TestAdvisoryWarns(unittest.TestCase):
    def test_allowlisted_kinds_do_not_warn(self):
        # ch. 06 / #13 / 2007 aren't even "numbers" (no $/%/×/decimal); ~2.0,
        # PEG < 1.0, and ≥50% are allowlisted. None should warn.
        self.assertEqual(warn_msgs(GOOD), [])

    def test_uncited_prose_number_warns(self):
        note = GOOD.replace("## Sources",
                            "Pre-tax income was $2.635B last year.\n\n## Sources")
        msgs = warn_msgs(note)
        self.assertTrue(any("2.635" in m for m in msgs), msgs)

    def test_number_present_in_table_is_not_warned(self):
        # $10.00 and 8.0% live in the table; referencing them in prose is fine.
        note = GOOD.replace("## 4. The numbers",
                            "The price is $10.00 and growth 8.0%.\n\n## 4. The numbers")
        self.assertEqual(warn_msgs(note), [])


class TestRealNotes(unittest.TestCase):
    def test_all_real_notes_are_structurally_complete(self):
        # A research NOTE is the .md half of a <TICKER>.md/<TICKER>.data.json
        # provenance pair; other markdown in research/ (e.g. lessons.md, the
        # append-only surprises journal) is not held to note structure.
        paths = sorted(p for p in glob.glob(os.path.join(RESEARCH, "*.md"))
                       if os.path.exists(p[:-3] + ".data.json"))
        self.assertTrue(paths, "no research/*.md found")
        for p in paths:
            with open(p) as fh:
                res = c.check_markdown(fh.read())
            self.assertEqual(res["fails"], [], f"{os.path.basename(p)}: {res['fails']}")


class TestCLI(unittest.TestCase):
    def _run(self, text, *args):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "note.md")
            with open(p, "w") as fh:
                fh.write(text)
            return subprocess.run([sys.executable, SCRIPT, *args, p],
                                  capture_output=True, text=True)

    def test_structural_fail_exits_1(self):
        r = self._run("no table, no sources\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", r.stdout)

    def test_warn_only_always_exits_0(self):
        r = self._run("no table, no sources\n", "--warn-only")
        self.assertEqual(r.returncode, 0)             # findings printed, but never blocks

    def test_good_note_exits_0(self):
        r = self._run(GOOD)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
