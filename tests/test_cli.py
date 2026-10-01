import tempfile
import unittest
from pathlib import Path

from quran_stat.cli import run
from quran_stat.io import read_verses, write_csv
from quran_stat.verify_plain_text import run as verify


class PipelineTests(unittest.TestCase):
    def test_csv_pipeline_and_independent_count(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "data" / "verses.csv"
            source.parent.mkdir()
            write_csv(source, ["Verse_ID", "Verse_Text"], [[1, "بَ أْ (1)"], [2, "بَرَّ (2)"]])
            out = directory / "results"
            report = run(source, out, plots=False)
            independent = verify(out)
            self.assertEqual(report["consistency"]["base_letters"], 4)
            self.assertEqual(independent["letter_total"], 4)
            self.assertEqual(independent["comparison_with_variation_csv"]["mismatches"], [])

    def test_source_directory_is_protected(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            with self.assertRaises(ValueError):
                run(directory / "verses.csv", directory)

    def test_invalid_csv_indices_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "verses.csv"
            write_csv(source, ["Verse_ID", "Verse_Text"], [[2, "بَ (1)"]])
            with self.assertRaises(ValueError):
                read_verses(source)


if __name__ == "__main__":
    unittest.main()
