import unittest

from quran_stat.annotations import find_unannotated, inspect_letter
from quran_stat.corpus import BASMALA, count_base_letters, split_verses
from quran_stat.statistics import describe


class AnalysisTests(unittest.TestCase):
    def test_verse_boundaries_and_unnumbered_basmala(self):
        self.assertEqual(
            split_verses(["سورة الفاتحة", BASMALA, BASMALA + " (1) نَصّ (2)", "تتمة"]),
            [BASMALA + " (1)", "نَصّ (2) تتمة"],
        )

    def test_count_excludes_tatweel_marks_and_number(self):
        self.assertEqual(count_base_letters("بِـئْر (12)"), 3)






    def test_historical_annotation_exceptions_and_nfc(self):
        findings, huruf = find_unannotated(["الشَّمْسِ (1)", "حم (1)", "ببَ (2)"])
        self.assertEqual([(r[0], r[2], r[3]) for r in findings], [(3, "ب", 0)])
        self.assertEqual([(r[0], r[2]) for r in huruf], [(2, "ح")])

    def test_immediate_haraka_and_end_of_text(self):
        result = inspect_letter("ئَ ئّ ئ", "ئ")
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["following_harakat"], {"fatha": 1, "shadda": 1})
        self.assertEqual(len(result["without_simple_haraka"]), 2)

    def test_statistics_ignore_zeros(self):
        result = describe({"a": 0, "b": 2, "c": 4})
        self.assertEqual(result["mean"], 3)
        self.assertEqual(result["q1"], 2.5)
        self.assertEqual(result["population_std"], 1)


if __name__ == "__main__":
    unittest.main()
