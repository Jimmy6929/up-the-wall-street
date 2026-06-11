"""Tests for scripts/watch-triggers (deterministic watchlist monitor).

Loaded by path (no .py extension). Network is stubbed at the `http` layer (not
at the functions under test - the first review caught a stubbed-over bug that
way: the XSL-prefixed primaryDocument fetched rendered HTML with no
<transactionCode> tags). The tests pin: the raw-XML URL fix, fire-once,
insider-buy gating with retry-on-unreadable, PER-TICKER baselining, price-rule
dedup + quote-date stamping, and the digest heartbeat. Offline, stdlib.
"""
import importlib.machinery
import importlib.util
import os
import unittest

PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "watch-triggers")
loader = importlib.machinery.SourceFileLoader("watch_triggers", PATH)
spec = importlib.util.spec_from_loader("watch_triggers", loader)
wt = importlib.util.module_from_spec(spec)
loader.exec_module(wt)

TRIGGERS = {"tickers": {
    "AAA": {"cik": 1, "watch_forms": ["10-Q", "8-K"], "insider_buys": True,
            "price_rules": [{"type": "price_below", "value": 50.0, "label": "test"}],
            "next_known_event": "Q2 ~2026-08-04"},
    "BBB": {"cik": 2, "watch_forms": ["10-K"], "insider_buys": False, "price_rules": []},
}}
BUY_XML = b"<doc><transactionCode>P</transactionCode></doc>"
SALE_XML = b"<doc><transactionCode>S</transactionCode></doc>"


def baselined_state():
    return {"seen_accessions": [], "baselined_tickers": ["AAA", "BBB"]}


class TestForm4RawXmlUrl(unittest.TestCase):
    """The regression from review: primaryDocument carries an XSL renderer
    prefix; fetching it verbatim returns HTML with zero transactionCode tags."""

    def setUp(self):
        self._http = wt.http
        self.urls = []

    def tearDown(self):
        wt.http = self._http

    def test_xsl_prefix_stripped_and_code_p_detected(self):
        def fake_http(url):
            self.urls.append(url)
            return BUY_XML
        wt.http = fake_http
        out = wt.form4_is_open_market_buy(1, "0001-23-000456", "xslF345X06/wk-form4_1.xml")
        self.assertTrue(out)
        self.assertIn("/000123000456/wk-form4_1.xml", self.urls[0])
        self.assertNotIn("xslF345X06", self.urls[0])

    def test_sale_is_false_and_unreadable_is_none(self):
        wt.http = lambda url: SALE_XML
        self.assertFalse(wt.form4_is_open_market_buy(1, "a-1", "f.xml"))
        def boom(url):
            raise OSError("net down")
        wt.http = boom
        self.assertIsNone(wt.form4_is_open_market_buy(1, "a-1", "f.xml"))


class TestTriggerLogic(unittest.TestCase):
    def setUp(self):
        self._saved = (wt.recent_filings, wt.http, wt.screening_price)
        self.filings = {1: [], 2: []}
        self.form4_xml = {}              # accession -> xml bytes (or raise)
        wt.recent_filings = self._recent
        wt.http = self._http
        wt.screening_price = lambda t: (60.0, "2026-06-10", None)

    def tearDown(self):
        wt.recent_filings, wt.http, wt.screening_price = self._saved

    def _recent(self, cik, limit=40):
        f = self.filings[cik]
        if f == "FAIL":
            raise OSError("EDGAR down")
        return f

    def _http(self, url):
        for acc_nodash, xml in self.form4_xml.items():
            if acc_nodash in url:
                if xml is None:
                    raise OSError("unreadable")
                return xml
        raise OSError(f"unexpected url {url}")

    # --- filings ------------------------------------------------------------
    def test_watched_filing_fires_once(self):
        self.filings[1] = [("10-Q", "acc-1", "2026-08-04", "doc.htm")]
        state = baselined_state()
        fired, _ = wt.check(TRIGGERS, state)
        self.assertEqual([(f["ticker"], f["kind"]) for f in fired], [("AAA", "filing:10-Q")])
        fired2, _ = wt.check(TRIGGERS, state)
        self.assertEqual(fired2, [])

    def test_unwatched_form_does_not_fire(self):
        self.filings[2] = [("8-K", "acc-2", "2026-08-04", "doc.htm")]   # BBB watches 10-K only
        fired, _ = wt.check(TRIGGERS, baselined_state())
        self.assertEqual(fired, [])

    def test_amended_form_matches_base(self):
        self.filings[2] = [("10-K/A", "acc-3", "2026-11-20", "doc.htm")]
        fired, _ = wt.check(TRIGGERS, baselined_state())
        self.assertEqual(fired[0]["kind"], "filing:10-K/A")

    # --- per-ticker baselining (the global-flag regression from review) ------
    def test_first_fetch_baselines_without_firing(self):
        self.filings[1] = [("10-Q", "old-1", "2026-01-01", "doc.htm")]
        state = {}                                       # nothing baselined yet
        fired, _ = wt.check(TRIGGERS, state)
        self.assertEqual(fired, [])                      # history swallowed
        self.assertIn("AAA", state["baselined_tickers"])

    def test_failed_baseline_does_not_fire_history_later(self):
        self.filings[1] = [("10-Q", "old-1", "2026-01-01", "doc.htm")]
        self.filings[2] = "FAIL"                         # BBB unreachable on run 1
        state = {}
        wt.check(TRIGGERS, state)
        self.assertNotIn("BBB", state["baselined_tickers"])
        self.filings[2] = [("10-K", "old-2", "2025-11-20", "doc.htm")]   # back up, run 2
        fired, _ = wt.check(TRIGGERS, state)
        self.assertEqual(fired, [])                      # BBB history must NOT fire
        self.filings[2] = [("10-K", "new-2", "2026-11-20", "doc.htm"),
                           ("10-K", "old-2", "2025-11-20", "doc.htm")]   # run 3: new filing
        fired, _ = wt.check(TRIGGERS, state)
        self.assertEqual([(f["ticker"], f["kind"]) for f in fired], [("BBB", "filing:10-K")])

    # --- insider buys ---------------------------------------------------------
    def test_form4_buy_fires_only_when_gated_on(self):
        self.filings[1] = [("4", "0001-23-000111", "2026-07-01", "xslF345X06/f4.xml")]
        self.filings[2] = [("4", "0001-23-000111", "2026-07-01", "xslF345X06/f4.xml")]
        self.form4_xml["000123000111"] = BUY_XML
        fired, _ = wt.check(TRIGGERS, baselined_state())
        self.assertEqual([(f["ticker"], f["kind"]) for f in fired], [("AAA", "insider-buy")])

    def test_form4_sale_marks_seen_silently(self):
        self.filings[1] = [("4", "0001-23-000222", "2026-07-01", "xslF345X06/f4.xml")]
        self.form4_xml["000123000222"] = SALE_XML
        state = baselined_state()
        fired, _ = wt.check(TRIGGERS, state)
        self.assertEqual(fired, [])
        self.assertIn("0001-23-000222", state["seen_accessions"])

    def test_unreadable_form4_retries_not_swallowed(self):
        self.filings[1] = [("4", "0001-23-000333", "2026-07-01", "xslF345X06/f4.xml")]
        self.form4_xml["000123000333"] = None            # unreadable on run 1
        state = baselined_state()
        fired, notes = wt.check(TRIGGERS, state)
        self.assertEqual(fired, [])
        self.assertNotIn("0001-23-000333", state["seen_accessions"])   # NOT swallowed
        self.assertTrue(any("unreadable" in n for n in notes))
        self.form4_xml["000123000333"] = BUY_XML         # readable on run 2 -> fires
        fired, _ = wt.check(TRIGGERS, state)
        self.assertEqual(fired[0]["kind"], "insider-buy")

    # --- price rules ----------------------------------------------------------
    def test_price_rule_fires_once_with_quote_date(self):
        wt.screening_price = lambda t: (49.0, "2026-06-10", None)
        state = baselined_state()
        fired, _ = wt.check(TRIGGERS, state)
        self.assertEqual(fired[0]["kind"], "valuation-threshold")
        self.assertIn("quote 2026-06-10", fired[0]["detail"])           # real quote date stamped
        fired2, _ = wt.check(TRIGGERS, state)
        self.assertEqual(fired2, [])                                    # deduped

    def test_no_price_source_is_a_note_not_a_crash(self):
        wt.screening_price = lambda t: (None, None, "yfinance not installed")
        fired, notes = wt.check(TRIGGERS, baselined_state())
        self.assertEqual(fired, [])
        self.assertTrue(any("yfinance" in n for n in notes))

    def test_unknown_rule_type_warns_instead_of_silently_ignoring(self):
        trig = {"tickers": {"AAA": {"cik": 1, "watch_forms": [], "insider_buys": False,
                "price_rules": [{"type": "price_abvoe", "value": 1, "label": "typo"}]}}}
        self.filings[1] = []
        fired, notes = wt.check(trig, {"seen_accessions": [], "baselined_tickers": ["AAA"]})
        self.assertEqual(fired, [])
        self.assertTrue(any("unknown price rule" in n for n in notes))

    # --- digest ----------------------------------------------------------------
    def test_digest_carries_next_known_event(self):
        line = wt.digest_line(TRIGGERS, {}, 0)
        self.assertIn("2 names watched", line)
        self.assertIn("Q2 ~2026-08-04", line)


if __name__ == "__main__":
    unittest.main()
