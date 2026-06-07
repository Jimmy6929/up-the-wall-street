"""Trap + behavior tests for universe_screen (the funnel discipline layer).

Runs entirely OFFLINE against tests/fixtures/*.json - no network, no rate limit.
The point is to prove the screen never ranks a name it shouldn't: cyclicals,
erratic earnings, dual-class, unsustainable growth, pre-revenue, and no-price
names must all be set aside, and only clean positive-earnings names ranked by
PEG. Stdlib unittest (no pytest), matching the repo's dependency-free ethos.

    python3 -m unittest discover -s .claude/skills/research/scripts -p 'test_*.py'
"""
import datetime as _dt
import os
import unittest

import universe_screen as u

FIX = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "tests", "fixtures")


class _FakeYF:
    """Minimal yfinance stand-in for attach_prices: every ticker resolves to a
    single close == `price` dated 2026-06-05. Lets the tests exercise the price
    guards and the offline-fixtures contract without touching the network."""

    def __init__(self, price):
        self._price = price

    def Ticker(self, ticker):                       # noqa: N802 - mimic yfinance API
        return _FakeYF._T(self._price)

    class _T:
        def __init__(self, price):
            self._price = price

        def history(self, period=None):
            return _FakeYF._Hist(self._price)

    class _Hist:
        def __init__(self, price):
            self._price = price

        def __len__(self):
            return 1

        def __getitem__(self, key):
            return _FakeYF._Col(self._price)

        @property
        def index(self):
            return _FakeYF._Idx()

    class _Col:
        def __init__(self, price):
            self.iloc = {-1: price}

    class _Idx:
        def __getitem__(self, i):
            return _dt.datetime(2026, 6, 5)


def _index(result):
    out = {}
    for bucket in ("ranked", "manual"):
        for r in result[bucket]:
            out[r["rec"]["ticker"]] = r
    return out


class TestFunnelDiscipline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = u.load_fixture_records(FIX)
        cls.result = u.screen_records(cls.records, years=5)
        cls.idx = _index(cls.result)
        cls.ranked_tickers = [r["rec"]["ticker"] for r in cls.result["ranked"]]

    # --- ranked names -------------------------------------------------------
    def test_clean_fast_grower_ranked_attractive(self):
        r = self.idx["GRND"]
        self.assertEqual(r["disposition"], "ranked")
        self.assertEqual(r["category"], "Fast grower")
        self.assertLess(r["metrics"]["peg"], 1.0)
        self.assertIn("peg_attractive", r["metrics"]["flags"])

    def test_stalwart_ranked_but_rich(self):
        r = self.idx["STAL"]
        self.assertEqual(r["disposition"], "ranked")
        self.assertEqual(r["category"], "Stalwart")
        self.assertIn("peg_rich", r["metrics"]["flags"])

    def test_ranked_sorted_by_peg_ascending(self):
        # cheaper-for-growth first: GRND (0.85) before STAL (3.07)
        self.assertEqual(self.ranked_tickers, ["GRND", "STAL"])

    # --- the traps: must NOT be ranked --------------------------------------
    def test_down_year_is_possible_cyclical_manual(self):
        r = self.idx["CYC"]
        self.assertEqual(r["disposition"], "manual")
        self.assertIn("possible_cyclical", r["reason"])

    def test_dual_class_manual(self):
        r = self.idx["DUAL"]
        self.assertEqual(r["disposition"], "manual")
        self.assertIn("multi-class", r["reason"])

    def test_unsustainable_growth_manual(self):
        # STAK is a cyclical at its peak. It is caught here ONLY because its CAGR
        # is absurd (~74%). A slower monotone-up cyclical (no down year, <50%
        # CAGR) would slip through to 'ranked' - the documented limit of EPS-only
        # detection; the qualitative /screen step is the real defense.
        r = self.idx["STAK"]
        self.assertEqual(r["disposition"], "manual")
        self.assertIn("unsustainable", r["reason"])

    def test_negative_earnings_dropped(self):
        self.assertIn("negative or zero TTM EPS (pre-revenue / turnaround)",
                      self.result["dropped_counts"])

    def test_no_price_dropped_not_ranked(self):
        self.assertIn("no price", self.result["dropped_counts"])
        self.assertNotIn("NOPX", self.ranked_tickers)

    def test_no_silent_exclusion(self):
        # every input lands in exactly one bucket; tallies account for all of them
        accounted = (len(self.result["ranked"]) + len(self.result["manual"])
                     + sum(self.result["dropped_counts"].values()))
        self.assertEqual(accounted, self.result["n_in"])

    # --- rendering / output -------------------------------------------------
    def test_scan_results_carries_disclaimer(self):
        md = u.render_scan_results(self.result, "2026-06-07")
        self.assertIn("NOT a backtester", md)
        self.assertIn("Manual review", md)

    def test_leads_rows_labeled_not_a_verdict(self):
        rows = u.render_leads_rows(self.result, top_n=40, date_str="2026-06-07")
        self.assertTrue(rows)
        for row in rows:
            self.assertIn("NOT a verdict", row)
            self.assertTrue(row.rstrip().endswith("| lead |"))


class TestGracefulDegradation(unittest.TestCase):
    def test_attach_prices_without_yfinance_keeps_fixture_prices(self):
        recs = [{"ticker": "A", "price": 10.0}, {"ticker": "B"}]
        saved = u.yf
        u.yf = None
        try:
            out, note = u.attach_prices(recs, sleep=0)
        finally:
            u.yf = saved
        self.assertEqual(out[0]["price"], 10.0)   # existing price preserved
        self.assertIsNone(out[1]["price"])         # missing -> None (will be dropped)
        self.assertIn("yfinance", note or "")


class TestPriceGuards(unittest.TestCase):
    """A bad price must never be valued/ranked - the regression behind the
    live-run artifacts (a $0 or preferred-share price producing a fake P/E)."""

    def _grower(self, ticker, price):
        return {"ticker": ticker, "company": ticker, "price": price,
                "eps_ttm": 2.0,
                "eps_history": {"2021": 1.0, "2022": 1.2, "2023": 1.45,
                                "2024": 1.7, "2025": 2.0}}

    def test_zero_price_dropped_not_ranked(self):
        res = u.screen_one(self._grower("ZERO", 0.0), years=5)
        self.assertEqual(res["disposition"], "dropped")

    def test_negative_price_dropped(self):
        res = u.screen_one(self._grower("NEG", -3.0), years=5)
        self.assertEqual(res["disposition"], "dropped")

    def test_positive_price_still_ranked(self):
        res = u.screen_one(self._grower("OK", 30.0), years=5)
        self.assertEqual(res["disposition"], "ranked")

    def test_attach_prices_rejects_nonpositive_quote(self):
        recs = [{"ticker": "BAD"}]
        saved = u.yf
        u.yf = _FakeYF(price=0.0)
        try:
            u.attach_prices(recs, sleep=0)
        finally:
            u.yf = saved
        self.assertIsNone(recs[0].get("price"))     # 0.0 quote rejected -> None


class TestCommonTickerPreference(unittest.TestCase):
    """_ticker_rank keeps the common-stock line when a CIK lists several tickers
    (the preferred/note-collision that produced the artifact 'bargains')."""

    def test_prefers_common_over_hyphen_preferred(self):
        self.assertLess(u._ticker_rank("WRB"), u._ticker_rank("WRB-PH"))
        self.assertLess(u._ticker_rank("CFR"), u._ticker_rank("CFR-PB"))

    def test_prefers_common_over_trailing_letter_note(self):
        self.assertLess(u._ticker_rank("TMUS"), u._ticker_rank("TMUSL"))
        self.assertLess(u._ticker_rank("SO"), u._ticker_rank("SOJD"))
        self.assertLess(u._ticker_rank("NTRS"), u._ticker_rank("NTRSO"))

    def test_name_match_breaks_same_length_bond_tie(self):
        # DTE common vs DTB baby bond: same length, no punctuation. The company
        # name's first token ("DTE ENERGY CO" -> "DTE") must break the tie toward
        # the common, not alphabetical "DTB" (the bug that ranked DTB #1).
        self.assertLess(u._ticker_rank("DTE", "DTE ENERGY CO"),
                        u._ticker_rank("DTB", "DTE ENERGY CO"))


class TestFixturesStayOffline(unittest.TestCase):
    def test_main_fixtures_does_not_clobber_prices(self):
        # With --fixtures, main() must NOT hit the network even when yfinance is
        # importable. A stub that would overwrite every price with a cheap 5.0
        # (making STAL look peg_attractive #1) proves it: the output must still
        # show STAL peg_rich, ranked BELOW GRND, from the fixtures' own prices.
        import contextlib
        import io
        import sys
        import tempfile
        saved_yf, saved_argv = u.yf, sys.argv
        tmp = tempfile.NamedTemporaryFile(suffix=".md", delete=False)
        tmp.close()
        u.yf = _FakeYF(price=5.0)
        sys.argv = ["universe_screen.py", "--fixtures", FIX, "--results", tmp.name]
        try:
            with contextlib.redirect_stdout(io.StringIO()):   # main() prints the table
                u.main()
            md = open(tmp.name).read()
        finally:
            u.yf, sys.argv = saved_yf, saved_argv
            os.unlink(tmp.name)
        self.assertIn("peg_rich", md)               # STAL kept its real (rich) price
        self.assertLess(md.find("GRND"), md.find("STAL"))   # GRND ranked first


class TestFixturesResultsPathIsolation(unittest.TestCase):
    def test_fixtures_run_does_not_clobber_real_scan_results(self):
        # A bare --fixtures run (no --results) must write scan-results.fixtures.md
        # and leave a real scan-results.md untouched - the regression that
        # destroyed the live sweep's provenance during verification.
        import contextlib
        import io
        import sys
        import tempfile
        saved_yf, saved_argv, saved_cwd = u.yf, sys.argv, os.getcwd()
        u.yf = None                                  # fixtures carry their own price
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "scan-results.md"), "w") as fh:
            fh.write("REAL SWEEP - DO NOT CLOBBER")
        sys.argv = ["universe_screen.py", "--fixtures", FIX]   # note: no --results
        try:
            os.chdir(d)
            with contextlib.redirect_stdout(io.StringIO()):
                u.main()
            self.assertTrue(os.path.exists(os.path.join(d, "scan-results.fixtures.md")))
            with open(os.path.join(d, "scan-results.md")) as fh:
                self.assertEqual(fh.read(), "REAL SWEEP - DO NOT CLOBBER")
        finally:
            u.yf, sys.argv = saved_yf, saved_argv
            os.chdir(saved_cwd)
            for f in ("scan-results.md", "scan-results.fixtures.md"):
                p = os.path.join(d, f)
                if os.path.exists(p):
                    os.remove(p)
            os.rmdir(d)


if __name__ == "__main__":
    unittest.main()
