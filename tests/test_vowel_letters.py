import unittest

from quran_stat.vowel_letters import analyze_vowel_letters


class VowelLettersTests(unittest.TestCase):
    def test_final_maqsoura_without_haraka(self):
        raw, retained, exclusions = analyze_vowel_letters("مُوسَى هُدًى (عَلَى)، فَتَى")
        self.assertEqual(raw["ى"], 4)
        self.assertEqual(retained["ى"], 4)
        self.assertFalse(exclusions)

    def test_maqsoura_with_each_haraka_is_not_retained(self):
        for mark in "ًٌٍَُِْ":
            with self.subTest(mark=mark):
                raw, retained, exclusions = analyze_vowel_letters("بَى" + mark)
                self.assertEqual(raw["ى"], 0)
                self.assertEqual(retained["ى"], 0)

    def test_nonfinal_maqsoura_and_shadda_dimension(self):
        raw, retained, exclusions = analyze_vowel_letters("بَىب بَىّ")
        self.assertEqual(raw["ى"], 2)
        self.assertEqual(retained["ى"], 1)
        self.assertEqual(exclusions[0]["reason"], "non_final_maqsoura")
        self.assertEqual(sum(raw.values()), sum(retained.values()) + len(exclusions))

    def test_article_with_marks_and_three_prefixes(self):
        raw, retained, exclusions = analyze_vowel_letters("الْكِتَابُ وَالْكِتَابُ فَالْكِتَابُ بِالْكِتَابِ")
        self.assertEqual(raw["ا"], 8)
        self.assertEqual(retained["ا"], 4)
        self.assertEqual([row["pattern"] for row in exclusions], ["ال", "وال", "فال", "بال"])

    def test_medial_alif_and_madda_retained(self):
        raw, retained, exclusions = analyze_vowel_letters("قَالَ آلَ يَقُولُ فِي")
        self.assertEqual(retained, {"ا": 1, "آ": 1, "و": 1, "ي": 1})
        self.assertEqual(raw, retained)
        self.assertFalse(exclusions)

    def test_fatha_refines_other_prefix_positions(self):
        raw, retained, exclusions = analyze_vowel_letters("كَالْكِتَابِ وَبِالْكِتَابِ")
        self.assertEqual(raw["ا"] - retained["ا"], 1)
        self.assertEqual(exclusions[0]["reason"], "no_preceding_fatha")
        self.assertEqual(exclusions[0]["previous_unit"], "بِ")

    def test_word_boundaries_and_vocalized_alif(self):
        raw, retained, exclusions = analyze_vowel_letters("(الْبَيْتِ)،الْبَابِ اَلْ")
        self.assertEqual(len(exclusions), 2)
        self.assertEqual(raw["ا"] - retained["ا"], 2)

    def test_accounting_identity(self):
        raw, retained, exclusions = analyze_vowel_letters("وَالْقَمَرِ فِي السَّمَاءِ")
        self.assertEqual(sum(raw.values()), sum(retained.values()) + len(exclusions))

    def test_previous_fatha_with_shadda_and_unicode_order(self):
        for word in ("نَّار", "نَّار"):
            raw, retained, exclusions = analyze_vowel_letters(word)
            self.assertEqual(retained["ا"], 1)
            self.assertFalse(exclusions)

    def test_fathatan_damma_and_word_boundary_do_not_qualify(self):
        raw, retained, exclusions = analyze_vowel_letters("قَالُوا كِتَابًا بَ ا بُا بَا")
        self.assertEqual(raw["ا"], 7)
        self.assertEqual(retained["ا"], 3)
        self.assertEqual(len(exclusions), 4)
        self.assertTrue(all(item["reason"] == "no_preceding_fatha" for item in exclusions))

    def test_fatha_on_article_prefix_does_not_reinstate_article(self):
        raw, retained, exclusions = analyze_vowel_letters("وَالْقَمَرِ فَالْقَمَرِ")
        self.assertEqual(raw["ا"], 2)
        self.assertEqual(retained["ا"], 0)
        self.assertTrue(all("َ" in item["previous_unit"] for item in exclusions))


if __name__ == "__main__":
    unittest.main()
