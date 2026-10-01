import unittest
from collections import Counter

from quran_stat.exhaustive import BASE_LETTERS, HARAKAT, build_catalog, count_exhaustive, letter_units, normalize


class ExhaustiveTests(unittest.TestCase):
    def test_complete_grid_including_zero_frequency_forms(self):
        catalog, counts, _, _ = count_exhaustive(["أَ"])
        self.assertEqual(len(catalog), len(set(BASE_LETTERS)) * 16)
        for letter in BASE_LETTERS:
            for haraka in HARAKAT:
                self.assertIn(normalize(letter + haraka), catalog)
                self.assertIn(normalize(letter + haraka + "ّ"), catalog)
        self.assertEqual(counts["أْ"], 0)

    def test_bare_letter_cannot_absorb_missing_vowel_patterns(self):
        _, counts, _, report = count_exhaustive(["أْ أً أٌ أ"])
        self.assertEqual({v: n for v, n in counts.items() if n}, {"أْ": 1, "أً": 1, "أٌ": 1, "أ": 1})
        self.assertEqual(report["difference"], 0)

    def test_shadda_is_not_one_of_seven_harakat(self):
        _, counts, _, _ = count_exhaustive(["ب بّ بَّ بَ"])
        self.assertEqual(counts["ب"], 1)
        self.assertEqual(counts["بّ"], 1)
        self.assertEqual(counts["بَّ"], 1)
        self.assertEqual(counts["بَ"], 1)

    def test_equivalent_diacritic_order_and_decomposed_hamza(self):
        self.assertEqual(Counter(letter_units("بَّ بَّ ا\u0654َ")), {"بَّ": 2, "أَ": 1})

    def test_composite_word_counted_as_two_letters(self):
        _, counts, _, report = count_exhaustive(["بَرَّ"])
        self.assertEqual(counts["بَ"], 1)
        self.assertEqual(counts["رَّ"], 1)
        self.assertNotIn("بَرَّ", counts)
        self.assertEqual(report["base_letters"], 2)
        self.assertTrue(report["accounting_valid"])

    def test_additional_marks_preserved_and_added_to_catalog(self):
        form = "هَ\u0670"
        catalog, counts, _, _ = count_exhaustive([form])
        self.assertIn(form, catalog)
        self.assertEqual(counts[form], 1)
        self.assertEqual(counts["هَ"], 0)
        self.assertEqual(counts["ه"], 0)

    def test_per_verse_total_and_boundaries(self):
        _, _, rows, report = count_exhaustive(["بَ (1)", "تْ ب (2)"])
        self.assertEqual([sum(row.values()) for row in rows], [1, 2])
        self.assertEqual(report["counted_units"], 3)


if __name__ == "__main__":
    unittest.main()
