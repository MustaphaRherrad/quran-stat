import unittest
from collections import Counter

from quran_stat.study import words_from_plain
from quran_stat.text_metrics import concentration, distribution, lexical_metrics, mattr, outlier_flags, zipf_fit


class TextMetricsTests(unittest.TestCase):
    def test_population_statistics(self):
        result = distribution([1, 2, 3, 4])
        self.assertEqual(result["median"], 2.5)
        self.assertEqual(result["q1"], 1.75)
        self.assertAlmostEqual(result["population_variance"], 1.25)
        self.assertEqual(result["mad"], 1)
        self.assertAlmostEqual(result["skewness"], 0)

    def test_outliers_and_zero_mad(self):
        result = distribution([1, 1, 1, 1, 100])
        flags = outlier_flags(100, result)
        self.assertTrue(flags["tukey"])
        self.assertTrue(flags["extreme"])
        self.assertIsNone(flags["modified_z"])
        self.assertIsNone(flags["mad_outlier"])

    def test_uniform_and_concentrated_entropy(self):
        uniform = concentration([10, 10, 10, 10])
        self.assertAlmostEqual(uniform["entropy_bits"], 2)
        self.assertAlmostEqual(uniform["effective_types"], 4)
        self.assertAlmostEqual(uniform["gini_observed_types"], 0)
        self.assertAlmostEqual(concentration([1, 3])["gini_observed_types"], 0.25)
        self.assertEqual(concentration([4])["entropy_bits"], 0)

    def test_mattr_against_explicit_windows(self):
        words = list("aababbccddabccca")
        for window in (1, 3, 5, len(words)):
            expected = sum(len(set(words[i:i + window])) / window for i in range(len(words) - window + 1)) / (len(words) - window + 1)
            self.assertAlmostEqual(mattr(words, window), expected)
        self.assertIsNone(mattr(words, 100))

    def test_lexical_types_hapax_and_yule(self):
        result = lexical_metrics(["a", "a", "b", "c"])
        self.assertEqual(result["ttr"], 0.75)
        self.assertEqual(result["hapax_types"], 2)
        self.assertEqual(result["dis_legomena_types"], 1)
        self.assertAlmostEqual(result["yule_k"], 1250)

    def test_zipf_exact_synthetic_curve(self):
        result = zipf_fit([120, 60, 40, 30])
        self.assertAlmostEqual(result["slope"], -1)
        self.assertAlmostEqual(result["r_squared"], 1)

    def test_word_segmentation_retains_clitics_and_letter_distinctions(self):
        self.assertEqual(words_from_plain("وبالحق، أ إ ا ة ه ى ي (23)"), ["وبالحق", "أ", "إ", "ا", "ة", "ه", "ى", "ي"])


if __name__ == "__main__":
    unittest.main()
