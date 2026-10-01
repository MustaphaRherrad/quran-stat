"""Alif sans haraka après fatha, hors article ; و et ي sans haraka ; آ séparée ; ى final sans haraka.

python -m quran_stat.count_vowel_letters
Il s'agit d'un critère graphique, pas d'une identification phonétique du madd.
"""

import argparse
import csv
from collections import Counter
from pathlib import Path

from .exhaustive import HARAKAT
from .io import write_csv, write_json
from .vowel_letters import analyze_vowel_letters


def run(directory):
    directory = Path(directory)
    totals, raw_totals = Counter(), Counter()
    per_verse = []
    excluded_rows = []
    with (directory / "verses.csv").open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            raw, counts, exclusions = analyze_vowel_letters(row["Verse_Text"])
            raw_totals.update(raw)
            for item in exclusions:
                excluded_rows.append([row["Verse_ID"], item["word"], item["pattern"], item["word_index_nfc"],
                                      item["reason"], item["previous_unit"], item["letter_index_in_word"], row["Verse_Text"]])
            totals.update(counts)
            per_verse.append([row["Verse_ID"], row["Verse_Text"], *(counts[c] for c in "اويآى"),
                              sum(counts[c] for c in "اويى"), sum(counts.values()), raw["ا"], len(exclusions)])
    # Vérifie le résultat par agrégation des colonnes du CSV déjà validé.
    comparison = Counter()
    with (directory / "quran_verse_variations_frequencies.csv").open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            for form, count in row.items():
                if form[0] in "اويآى" and not any(mark in HARAKAT for mark in form[1:]):
                    comparison[form[0]] += int(count)
    if comparison != raw_totals:
        raise ValueError("Le texte et le CSV des variations donnent des résultats différents.")
    write_csv(directory / "vowel_letters_by_verse.csv",
              ["Verse_ID", "Verse_Text", "ا", "و", "ي", "آ", "ى", "Total_without_madda", "Total_with_madda", "Raw_alif", "Excluded_alif"], per_verse)
    exclusion_header = ["Verse_ID", "Word", "Pattern", "Word_Index_NFC", "Reason", "Previous_Unit", "Letter_Index_In_Word", "Verse_Text"]
    write_csv(directory / "excluded_alifs.csv", exclusion_header, excluded_rows)
    write_csv(directory / "excluded_article_alifs.csv",
              exclusion_header, [row for row in excluded_rows if row[4] == "article"])
    report = {
        "criterion": "ا without seven harakat, preceded by fatha in the same word, excluding initial ال or وال / فال / بال; و ي without seven harakat; آ separately; final ى without seven harakat (no condition on preceding marks); graphical rule",
        "raw_counts_without_seven_harakat": dict(raw_totals),
        "counts_without_seven_harakat": dict(totals),
        "excluded_alifs": len(excluded_rows),
        "excluded_by_reason": dict(Counter(row[4] for row in excluded_rows)),
        "excluded_article_alifs": sum(row[4] == "article" for row in excluded_rows),
        "excluded_by_article_pattern": dict(Counter(row[2] for row in excluded_rows if row[4] == "article")),
        "total_without_madda": sum(totals[c] for c in "اويى"),
        "total_with_madda": sum(totals.values()),
        "raw_counts_match_variation_csv": comparison == raw_totals,
        "corrected_plus_exclusions_match_raw": sum(totals.values()) + len(excluded_rows) == sum(raw_totals.values()),
    }
    write_json(directory / "vowel_letters_summary.json", report)
    print(f"Prolongations selon les critères retenus : {report['total_with_madda']} ; alifs exclus : {len(excluded_rows)}.")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    run(parser.parse_args().output_dir)


if __name__ == "__main__":
    main()
