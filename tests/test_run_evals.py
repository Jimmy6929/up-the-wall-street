"""Tests for the eval harness's deterministic layer (evals/run_evals.py).

Only the pure/grading functions are tested - never the headless runner or the
LLM judge (those cost tokens and are exercised by actually running
scripts/evals). Stdlib unittest, offline, like the rest of the repo.
"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "evals"))

import run_evals as rv   # noqa: E402

NOTE = """---
title: STAK — Continental Steel & Auto
ticker: STAK
category: Cyclical
verdict: Pass/Avoid
---

# STAK — Continental Steel & Auto

## 4. The numbers
| Metric | Value | Source | As of |
|---|---|---|---|
| Price | 60.0 | user-provided | 2026-06-06 |
| P/E | 6.0 | computed | 2026-06-06 |
| **PEG** | 0.75 | computed — misleading for a cyclical | 2026-06-06 |

## 6. Bear case (the skeptic)
Earnings fall when the cycle turns.

## Sources
- user-provided eval fixture (2026-06-06)
"""


class TestFrontmatterAndVerdicts(unittest.TestCase):
    def test_parse_frontmatter(self):
        fm = rv.parse_frontmatter(NOTE)
        self.assertEqual(fm["category"], "Cyclical")
        self.assertEqual(fm["verdict"], "Pass/Avoid")

    def test_canon_verdict_variants(self):
        self.assertEqual(rv.canon_verdict("Buy candidate"), "Buy candidate")
        self.assertEqual(rv.canon_verdict("WATCHLIST"), "Watchlist")
        self.assertEqual(rv.canon_verdict("Pass"), "Pass/Avoid")
        self.assertEqual(rv.canon_verdict("Avoid"), "Pass/Avoid")
        self.assertEqual(rv.canon_verdict(None), "")


class TestNumInText(unittest.TestCase):
    def test_accepts_common_formats(self):
        self.assertTrue(rv.num_in_text("P/E is 6.0 here", 6.0))
        self.assertTrue(rv.num_in_text("P/E is 6 here", 6.0))
        self.assertTrue(rv.num_in_text("PEG 0.75 (rich)", 0.75))
        self.assertTrue(rv.num_in_text("anything", None))   # nothing computed -> vacuous

    def test_rejects_missing_number(self):
        self.assertFalse(rv.num_in_text("the multiple is modest", 6.0))

    def test_accepts_shown_precision_rounding(self):
        self.assertTrue(rv.num_in_text("6.00", 6.0))
        self.assertTrue(rv.num_in_text("P/E ~24", 24.44))
        self.assertTrue(rv.num_in_text("1,100", 1100.0))

    def test_rejects_substring_collisions_and_drift(self):
        # the anti-hallucination seam: a different number NEVER matches,
        # even when the computed value is a substring of the shown one
        self.assertFalse(rv.num_in_text("6.4", 6.0))      # hand-computed drift
        self.assertFalse(rv.num_in_text("16.0", 6.0))     # substring collision
        self.assertFalse(rv.num_in_text("26.05", 6.0))    # substring collision
        self.assertFalse(rv.num_in_text("112.5", 12.0))   # substring collision
        self.assertFalse(rv.num_in_text("10.75", 0.75))   # substring collision
        self.assertFalse(rv.num_in_text("12.8", 12.0))    # bare-int form leak


class TestMetricContract(unittest.TestCase):
    """Shown numbers must match the script; an honest n/a passes; a different
    number (model arithmetic) never does; a missing table row fails."""

    def test_table_value_finds_the_peg_row_not_div_adj(self):
        self.assertEqual(rv.table_value(NOTE, "PEG"), "0.75")
        self.assertEqual(rv.table_value(NOTE, "P/E"), "6.0")

    def test_matching_and_na_pass(self):
        self.assertTrue(rv.metric_matches("6.0", 6.0))
        self.assertTrue(rv.metric_matches("n/a (cyclical)", 0.75))
        self.assertTrue(rv.metric_matches("anything", None))

    def test_wrong_number_or_missing_row_fail(self):
        self.assertFalse(rv.metric_matches("5.9", 6.0))     # hand-computed drift
        self.assertFalse(rv.metric_matches("6.4", 6.0))     # hand-computed drift
        self.assertFalse(rv.metric_matches("16.0", 6.0))    # substring collision
        self.assertFalse(rv.metric_matches("112.5", 12.0))  # substring collision
        self.assertFalse(rv.metric_matches(None, 6.0))      # row missing


class TestJudgeJsonExtraction(unittest.TestCase):
    def test_strips_code_fences_and_prefix(self):
        raw = 'Here you go:\n```json\n{"items": [{"i": 0, "pass": true}]}\n```'
        self.assertTrue(rv.extract_json(raw)["items"][0]["pass"])

    def test_raises_on_garbage(self):
        with self.assertRaises(ValueError):
            rv.extract_json("no json here")


class TestCaseSelection(unittest.TestCase):
    def test_smoke_selects_only_traps(self):
        cases = rv.load_cases(smoke=True)
        self.assertTrue(cases)
        self.assertTrue(all(c.get("trap") for c in cases))

    def test_filter_by_prefix(self):
        cases = rv.load_cases(only="03")
        self.assertEqual(len(cases), 1)
        self.assertIn("cyclical", cases[0]["name"])

    def test_all_cases_carry_grade_config(self):
        # every case must say how it is code-graded (additive labels; the frozen
        # expected_behavior lists are untouched and judge-graded)
        for c in rv.load_cases():
            self.assertIn("grade", c, c["_file"])


class TestCodeGrade(unittest.TestCase):
    def _case(self):
        with open(os.path.join(rv.CASES_DIR, "03-cyclical-peak-trap.json")) as fh:
            case = json.load(fh)
        case["_file"] = "03-cyclical-peak-trap.json"
        return case

    def test_grades_a_good_note(self):
        case = self._case()
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "STAK.md"), "w") as fh:
                fh.write(NOTE)
            checks = {c["check"]: c["pass"] for c in rv.code_grade(case, d, "")}
        self.assertTrue(checks["category"])
        self.assertTrue(checks["verdict"])
        self.assertTrue(checks["metric:pe"])     # 6.0 appears in the note
        self.assertTrue(checks["bear-case"])

    def test_category_parenthetical_qualifiers_match_on_head(self):
        # "Avoid (hype over fundamentals)" vs truth "Avoid (hottest stock...)" is the
        # same category judgment — the grader must not fail on qualifier wording
        # (the over-rigid-grader trap from the first smoke run)
        with open(os.path.join(rv.CASES_DIR, "04-hot-stock-avoid.json")) as fh:
            case = json.load(fh)
        case["_file"] = "04-hot-stock-avoid.json"
        note = NOTE.replace("category: Cyclical", "category: Avoid (hype over fundamentals)") \
                   .replace("ticker: STAK", "ticker: NOVA")
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "NOVA.md"), "w") as fh:
                fh.write(note)
            checks = {c["check"]: c["pass"] for c in rv.code_grade(case, d, "")}
        self.assertTrue(checks["category"])

    def test_fails_wrong_category_and_buy_verdict(self):
        case = self._case()
        bad = NOTE.replace("category: Cyclical", "category: Stalwart") \
                  .replace("verdict: Pass/Avoid", "verdict: Buy candidate")
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "STAK.md"), "w") as fh:
                fh.write(bad)
            checks = {c["check"]: c["pass"] for c in rv.code_grade(case, d, "")}
        self.assertFalse(checks["category"])     # the cyclical trap: never a stalwart
        self.assertFalse(checks["verdict"])      # never a Buy at the peak

    def test_missing_note_fails_when_required(self):
        case = self._case()
        with tempfile.TemporaryDirectory() as d:
            checks = rv.code_grade(case, d, "")
        self.assertEqual(len(checks), 1)
        self.assertFalse(checks[0]["pass"])

    def test_conversational_case_needs_no_note(self):
        with open(os.path.join(rv.CASES_DIR, "06-derivatives-out-of-scope.json")) as fh:
            case = json.load(fh)
        case["_file"] = "06-derivatives-out-of-scope.json"
        with tempfile.TemporaryDirectory() as d:
            checks = rv.code_grade(case, d, "I can't research the option (ch. 19)...")
        self.assertTrue(all(c["pass"] for c in checks))


if __name__ == "__main__":
    unittest.main()
