"""Tests for validate_data.py - the anti-hallucination schema/provenance gate.

Two jobs: (1) prove the gate FAILS CLOSED (missing required fields, unsourced
values, bad category are errors), and (2) regression-pin that every real
research/*.data.json still validates - so a hand-edit that drops a source can't
land silently. Stdlib unittest, offline.

    python3 -m unittest discover -s .claude/skills/research/scripts -p 'test_*.py'
"""
import datetime
import glob
import json
import os
import subprocess
import sys
import tempfile
import unittest

import validate_data as v

REPO = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
RESEARCH = os.path.join(REPO, "research")
SCRIPT = os.path.join(os.path.dirname(__file__), "validate_data.py")
TODAY = datetime.date(2026, 6, 8)


def _doc(**top_overrides):
    """A fresh, fully-valid document each call (mutate it per test)."""
    doc = {
        "ticker": "TEST", "company": "Test Co", "category": "Stalwart",
        "source": "SEC EDGAR companyfacts", "as_of": "2026-06-01",
        "inputs": {
            "price": {"value": 10.0, "source": "web quote", "as_of": "2026-06-01"},
            "eps_ttm": {"value": 1.0, "source": "SEC EDGAR", "as_of": "2026-03-31"},
            "eps_history": {"value": {"2022": 0.8, "2023": 0.9, "2024": 1.0},
                            "source": "SEC EDGAR", "as_of": "2024-12-31"},
            "shares_outstanding": {"value": 100, "source": "SEC EDGAR", "as_of": "2026-03-31"},
            "total_debt": {"value": 0, "source": "SEC EDGAR", "as_of": "2026-03-31"},
            "cash": {"value": 50, "source": "SEC EDGAR", "as_of": "2026-03-31"},
            "dividend_per_share": {"value": 0.2, "source": "SEC EDGAR", "as_of": "2025-12-31"},
            "long_term_growth_estimate_pct": {"value": 8.0, "source": "est", "as_of": "2026-06-01"},
            "institutional_ownership_pct": {"value": 60.0, "source": "MarketBeat", "as_of": "2026-06"},
            "insider_activity": {"value": "net buying", "source": "Form 4", "as_of": "2026-06-01"},
        },
    }
    doc.update(top_overrides)
    return doc


class TestCleanAndRealFiles(unittest.TestCase):
    def test_clean_doc_validates(self):
        r = v.validate_doc(_doc(), today=TODAY)
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["errors"], [])

    def test_all_research_data_files_validate(self):
        paths = sorted(glob.glob(os.path.join(RESEARCH, "*.data.json")))
        self.assertTrue(paths, "no research/*.data.json found")
        for p in paths:
            res = v.validate_file(p)
            self.assertTrue(res["ok"], f"{os.path.basename(p)} failed: {res['errors']}")


class TestFailsClosed(unittest.TestCase):
    """The senior-engineer contract: missing/unsourced data must be an error."""

    def test_missing_required_field_is_error(self):
        d = _doc()
        d["inputs"].pop("price")
        r = v.validate_doc(d, today=TODAY)
        self.assertFalse(r["ok"])
        self.assertTrue(any("price" in e for e in r["errors"]))

    def test_null_required_field_counts_as_missing(self):
        d = _doc()
        d["inputs"]["eps_ttm"] = {"value": None, "source": "x", "as_of": "2026-06-01"}
        r = v.validate_doc(d, today=TODAY)
        self.assertFalse(r["ok"])
        self.assertTrue(any("eps_ttm" in e for e in r["errors"]))

    def test_unsourced_numeric_value_is_error(self):
        d = _doc()
        d.pop("source")                                 # no top-level provenance to fall back on
        d.pop("as_of")
        d["inputs"]["price"] = {"value": 10.0}          # and no field-level provenance
        r = v.validate_doc(d, today=TODAY)
        self.assertFalse(r["ok"])
        self.assertTrue(any("price" in e and "source/as_of" in e for e in r["errors"]))

    def test_unsourced_qualitative_value_is_error(self):
        d = _doc()
        d.pop("source")
        d.pop("as_of")
        d["inputs"]["insider_activity"] = {"value": "net selling"}   # prose, but unsourced
        r = v.validate_doc(d, today=TODAY)
        self.assertFalse(r["ok"])
        self.assertTrue(any("insider_activity" in e for e in r["errors"]))

    def test_top_level_provenance_satisfies_unsourced_field(self):
        d = _doc()                                       # keeps top-level source+as_of
        d["inputs"]["price"] = {"value": 10.0}           # no field prov, but top prov exists
        r = v.validate_doc(d, today=TODAY)
        self.assertTrue(r["ok"], r["errors"])


class TestCategory(unittest.TestCase):
    def test_invalid_category_is_error(self):
        r = v.validate_doc(_doc(category="Mega grower"), today=TODAY)
        self.assertFalse(r["ok"])
        self.assertTrue(any("category" in e for e in r["errors"]))

    def test_parenthetical_qualifier_is_accepted(self):
        # RKLB's real category - a canonical base with a qualifier - must pass.
        r = v.validate_doc(_doc(category="Fast grower (unprofitable / negative EPS)"), today=TODAY)
        self.assertTrue(r["ok"], r["errors"])

    def test_missing_category_warns_not_errors(self):
        d = _doc()
        d.pop("category")
        r = v.validate_doc(d, today=TODAY)
        self.assertTrue(r["ok"])
        self.assertTrue(any("category" in w for w in r["warnings"]))


class TestExplicitNulls(unittest.TestCase):
    def test_documented_null_is_not_flagged_missing(self):
        # A cyclical's n/m forward growth: null WITH a documented reason is the
        # disciplined state, not an omission - it must not warn "missing".
        d = _doc()
        d["inputs"]["long_term_growth_estimate_pct"] = {
            "value": None, "source": "n/m off a single recovery year", "as_of": "2026-06-01"}
        r = v.validate_doc(d, today=TODAY)
        self.assertTrue(r["ok"], r["errors"])
        self.assertFalse(any("long_term_growth_estimate_pct" in w for w in r["warnings"]),
                         r["warnings"])

    def test_null_without_reason_warns(self):
        d = _doc()
        d["inputs"]["cash"] = {"value": None}            # null, no reason
        r = v.validate_doc(d, today=TODAY)
        self.assertTrue(r["ok"])                          # a gap is a warning, not an error
        self.assertTrue(any("cash" in w for w in r["warnings"]))


class TestStaleness(unittest.TestCase):
    def test_old_data_warns(self):
        r = v.validate_doc(_doc(as_of="2024-01-01"), today=TODAY)
        self.assertTrue(any("old" in w for w in r["warnings"]))


class TestCLI(unittest.TestCase):
    """The CLI surface: legacy single-file JSON, and bulk exit semantics."""

    def test_single_file_emits_legacy_json_object(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "g.data.json")
            with open(p, "w") as fh:
                json.dump(_doc(), fh)
            r = subprocess.run([sys.executable, SCRIPT, p], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        out = json.loads(r.stdout)                        # still a single parseable object
        self.assertTrue(out["ok"])
        self.assertEqual(out["errors"], [])

    def test_bulk_exits_1_when_any_file_fails(self):
        good = _doc()
        bad = _doc()
        bad["inputs"].pop("price")
        with tempfile.TemporaryDirectory() as d:
            gp, bp = os.path.join(d, "good.data.json"), os.path.join(d, "bad.data.json")
            with open(gp, "w") as fh:
                json.dump(good, fh)
            with open(bp, "w") as fh:
                json.dump(bad, fh)
            r = subprocess.run([sys.executable, SCRIPT, gp, bp], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", r.stdout)


if __name__ == "__main__":
    unittest.main()
