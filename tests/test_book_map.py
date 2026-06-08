"""Deterministic fidelity check for playbook/00a-book-map.md.

The book map is the traceability record between *One Up on Wall Street* and this
agent's workflow. This test is the "deterministic" half of the layered
enforcement (the rubric/eval cases are the other half): it fails loudly if the
map silently loses a chapter, marks a step MISSING, or points at a file that no
longer exists. It uses only the standard library.

Run: ``python3 tests/test_book_map.py``  (or via pytest).
"""

import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK_MAP = os.path.join(REPO_ROOT, "playbook", "00a-book-map.md")

# All 21 chapters of the Millennium Edition: Introduction (00) + chapters 01-20.
EXPECTED_CHAPTERS = {f"{i:02d}" for i in range(21)}

# The nine signature concept notes; each must keep a row in the map.
EXPECTED_CONCEPTS = [
    "Invest in What You Know",
    "The Six Categories of Stocks",
    "The Perfect Stock",
    "Stocks to Avoid",
    "The Two-Minute Drill",
    "The PEG Ratio",
    "The Final Checklist",
    "The Tenbagger",
    "Watering the Weeds",
]

VALID_STATUSES = {"FAITHFUL", "PARTIAL", "MISSING"}

# Top-level repo locations a backticked path may legitimately point into.
PATH_ROOTS = ("playbook/", ".claude/", "templates/", "evals/", "tests/", "research/")
BARE_FILES = {"CLAUDE.md", "README.md", "leads.md", "watchlist.md", "portfolio.md"}

PATH_RE = re.compile(r"`([A-Za-z0-9._/-]+\.(?:md|py|json))`")


def _read_map():
    with open(BOOK_MAP, encoding="utf-8") as fh:
        return fh.read()


def _table_rows(text):
    """Yield lists of stripped cells for every markdown table row."""
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        # Skip header separator rows like | --- | --- |.
        if all(set(c) <= {"-", ":"} and c for c in cells):
            continue
        yield cells


class BookMapTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(os.path.exists(BOOK_MAP), f"missing {BOOK_MAP}")
        self.text = _read_map()

    def test_all_chapters_present(self):
        found = set()
        for cells in _table_rows(self.text):
            if cells and re.fullmatch(r"\d{2}", cells[0]):
                found.add(cells[0])
        missing = EXPECTED_CHAPTERS - found
        self.assertFalse(missing, f"chapters with no row in the book map: {sorted(missing)}")

    def test_all_concepts_present(self):
        for concept in EXPECTED_CONCEPTS:
            self.assertIn(
                concept, self.text, f"concept note dropped from the book map: {concept!r}"
            )

    def test_no_missing_status(self):
        statuses = []
        for cells in _table_rows(self.text):
            if cells and cells[-1] in VALID_STATUSES:
                statuses.append(cells[-1])
        # Every chapter + concept + the modern-app row carries a status.
        self.assertGreaterEqual(
            len(statuses), len(EXPECTED_CHAPTERS) + len(EXPECTED_CONCEPTS),
            "fewer status cells than chapters + concepts — table format drifted",
        )
        missing = [s for s in statuses if s == "MISSING"]
        self.assertFalse(
            missing,
            "the book map has MISSING rows — a chapter/concept step lost its home in the workflow",
        )

    def test_referenced_files_exist(self):
        dangling = []
        for token in set(PATH_RE.findall(self.text)):
            checkable = token in BARE_FILES or token.startswith(PATH_ROOTS)
            if not checkable:
                continue
            if not os.path.exists(os.path.join(REPO_ROOT, token)):
                dangling.append(token)
        self.assertFalse(dangling, f"book map references files that don't exist: {sorted(dangling)}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
