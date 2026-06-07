"""Characterization tests for compute_valuation.compute().

These lock the deterministic valuation math against the five eval fixtures so a
refactor (e.g. extracting compute() so universe_screen.py can import it) can
never silently move a number. If one of these fails, the math changed - that is
the whole point of this guard. The expected values mirror the assertions in the
fixtures' own `expected_behavior` blocks.

Stdlib unittest (no pytest) to keep the repo dependency-free. Run either:
    python3 -m unittest discover -s .claude/skills/research/scripts -p 'test_*.py'
    pytest .claude/skills/research/scripts        # also works if pytest present
"""
import json
import os
import unittest

import compute_valuation as cv

CASES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "evals", "cases")


def _run(fixture, category=None):
    """Resolve a fixture the way compute_valuation.main() does, then compute."""
    with open(os.path.join(CASES_DIR, fixture)) as fh:
        doc = json.load(fh)
    data = doc.get("given_facts") or doc.get("inputs") or doc
    category = category or doc.get("category") or cv.get_value(data, "category")
    return cv.compute(data, category)


# (fixture, pe, growth_used_pct, peg, dividend_adjusted_peg, net_cash_per_share,
#  must-contain flags)
EXPECTED = [
    ("01-stalwart-clean.json",    25.16, 9,    2.8,  0.44,  -6.19, {"peg_rich"}),
    ("02-fast-grower.json",       22.5,  25,   0.9,  1.11,   1.33, {"peg_attractive"}),
    ("03-cyclical-peak-trap.json", 6.0,  8,    0.75, 1.89,  -21.0, {"peg_attractive", "insider_selling"}),
    ("04-hot-stock-avoid.json",   90.0,  80,   1.12, 0.89,   4.67, {"unsustainable_growth", "crowded_ownership", "insider_selling"}),
]


class TestComputeCharacterization(unittest.TestCase):
    def test_fixture_metrics(self):
        for fixture, pe, growth, peg, dapeg, ncps, flags in EXPECTED:
            with self.subTest(fixture=fixture):
                out = _run(fixture)
                self.assertEqual(out["pe"], pe)
                self.assertEqual(out["growth_used_pct"], growth)
                self.assertEqual(out["peg"], peg)
                self.assertEqual(out["dividend_adjusted_peg"], dapeg)
                self.assertEqual(out["net_cash_per_share"], ncps)
                self.assertTrue(
                    flags.issubset(set(out["flags"])),
                    msg=f"{fixture}: missing {flags - set(out['flags'])}")

    def test_whisper_negative_earnings(self):
        """05: EPS <= 0 -> no earnings-based valuation, no debt."""
        out = _run("05-whisper-stock-avoid.json")
        self.assertIsNone(out["pe"])
        self.assertIsNone(out["peg"])
        self.assertIsNone(out["dividend_adjusted_peg"])
        self.assertIn("negative_or_zero_earnings", out["flags"])
        self.assertIn("no_debt", out["flags"])

    def test_cyclical_caveat_suppresses_peg_attractive(self):
        """The trap: case 03 has a low PEG (0.75) that reads 'attractive' until it
        is classified Cyclical, at which point the caveat fires and the attractive
        flag must NOT appear (a low P/E on peak earnings is a danger sign, ch.15)."""
        out = _run("03-cyclical-peak-trap.json", category="Cyclical")
        self.assertIn("cyclical_caveat", out["flags"])
        self.assertNotIn("peg_attractive", out["flags"])
        self.assertEqual(out["peg"], 0.75)  # still computed, interpretation withheld


if __name__ == "__main__":
    unittest.main()
