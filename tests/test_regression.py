"""Régressions sur le corpus public ; aucune dépendance aux fichiers Colab."""

import hashlib
import json
import unittest
from pathlib import Path

from quran_stat.annotations import find_unannotated
from quran_stat.corpus import split_verses
from quran_stat.io import read_paragraphs, read_verses
from quran_stat.exhaustive import count_exhaustive
from quran_stat.vowel_letters import analyze_vowel_letters

ROOT = Path(__file__).resolve().parents[1]


class CorpusRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verses = read_verses(ROOT / "data/verses.csv")

    def test_corpus_integrity(self):
        manifest = json.loads((ROOT / "data/manifest.json").read_text())
        self.assertEqual(hashlib.sha256((ROOT / "data/verses.csv").read_bytes()).hexdigest(), manifest["sha256"])
        self.assertEqual(len(self.verses), 6236)

    @unittest.skipUnless((ROOT / "local/quran.docx").exists(), "Document Word local facultatif")
    def test_local_word_matches_public_corpus(self):
        self.assertEqual(split_verses(read_paragraphs(ROOT / "local/quran.docx")), self.verses)

    def test_annotation_candidates(self):
        findings, _ = find_unannotated(self.verses)
        self.assertEqual(len(findings), 6)
        self.assertTrue(all(row[1][row[3]] == row[2] for row in findings))

    def test_exhaustive_corpus(self):
        catalog, counts, per_verse, report = count_exhaustive(self.verses)
        self.assertEqual(len(catalog), 576)
        self.assertEqual(sum(counts.values()), 330705)
        self.assertEqual(counts["أ"], 0)
        self.assertEqual(counts["أْ"], 509)
        self.assertEqual(counts["أً"], 4)
        self.assertEqual(counts["أٌ"], 3)
        self.assertTrue(report["accounting_valid"])
        self.assertEqual(report["difference"], 0)
        self.assertEqual(sum(sum(row.values()) for row in per_verse), 330705)

    def test_vowel_letter_filters(self):
        from collections import Counter
        totals, reasons = Counter(), Counter()
        for verse in self.verses:
            _, retained, exclusions = analyze_vowel_letters(verse)
            totals.update(retained)
            reasons.update(item["reason"] for item in exclusions)
        self.assertEqual(totals, {"ا": 24124, "و": 10034, "ي": 9857, "آ": 1511, "ى": 2592})
        self.assertEqual(reasons, {"article": 11958, "no_preceding_fatha": 7458})


if __name__ == "__main__":
    unittest.main()
