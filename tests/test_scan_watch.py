"""Tests for scripts/scan-watch (display-only progress view for /scan).

The script has no .py extension, so it's loaded by path. Only the pure
parsing/rendering functions are tested - never the animation loop.
"""
import importlib.machinery
import importlib.util
import os
import unittest

PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "scan-watch")
loader = importlib.machinery.SourceFileLoader("scan_watch", PATH)
spec = importlib.util.spec_from_loader("scan_watch", loader)
sw = importlib.util.module_from_spec(spec)
loader.exec_module(sw)


class TestStatusParsing(unittest.TestCase):
    def test_phases_in_order(self):
        self.assertEqual(sw.status(""), ("starting", 0, 0))
        self.assertEqual(sw.status("# Stage A: 2033 survivors from frames"),
                         ("stage A done", 0, 2033))
        text = "# Stage A: 2033 survivors\n# fundamentals: 300/2033\n"
        self.assertEqual(sw.status(text), ("fundamentals", 300, 2033))
        text += "# prices: 50/1900\n# prices: 75/1900\n"
        self.assertEqual(sw.status(text), ("pricing", 75, 1900))  # latest marker wins

    def test_done_only_on_final_markdown(self):
        self.assertFalse(sw.is_done("# prices: 1900/1900"))
        self.assertTrue(sw.is_done("# prices: 1900/1900\n# Scan results - 2026-06-10\n"))


class TestRendering(unittest.TestCase):
    def test_bar_bounds(self):
        self.assertEqual(sw.bar(0, 100), "." * sw.BAR_WIDTH)
        self.assertEqual(sw.bar(100, 100), "#" * sw.BAR_WIDTH)
        self.assertEqual(sw.bar(0, 0), "." * sw.BAR_WIDTH)      # unknown total
        self.assertEqual(sw.bar(150, 100), "#" * sw.BAR_WIDTH)  # clamped, never overflows

    def test_line_shows_progress_and_completion(self):
        running = sw.line("# prices: 950/1900", elapsed_s=125, tick=0)
        self.assertIn(" 50%", running)
        self.assertIn("(950/1900)", running)
        self.assertIn("2m05s", running)
        done = sw.line("# prices: 1900/1900\n# Scan results - 2026-06-10", 600, 0)
        self.assertIn("complete", done)
        self.assertIn("✓", done)


if __name__ == "__main__":
    unittest.main()
