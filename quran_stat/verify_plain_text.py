"""Vérification indépendante à partir du texte de outputs/verses.csv.

Exécuter : python3 -m quran_stat.verify_plain_text
Aucun catalogue ni fonction de comptage du pipeline n'est utilisé.
"""

import argparse
import csv
import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path

MARKS = "ًٌٍَُِّْ"


def strip_verses(source, target):
    """Supprime uniquement les sept harakat et la shadda, sans normalisation."""
    removed = Counter()
    translation = str.maketrans("", "", MARKS)
    with source.open(encoding="utf-8-sig", newline="") as src, target.open("w", encoding="utf-8-sig", newline="") as dst:
        reader = csv.DictReader(src)
        writer = csv.DictWriter(dst, fieldnames=["Verse_ID", "Verse_Text"])
        writer.writeheader()
        for row in reader:
            text = row["Verse_Text"]
            removed.update(char for char in text if char in MARKS)
            writer.writerow({"Verse_ID": row["Verse_ID"], "Verse_Text": text.translate(translation)})
    return removed


def count_plain_verses(source, target):
    """Relit le fichier sans harakat ; classe les lettres par catégorie Unicode."""
    letters, excluded = Counter(), Counter()
    counts = {}
    with source.open(encoding="utf-8-sig", newline="") as src, target.open("w", encoding="utf-8-sig", newline="") as dst:
        writer = csv.writer(dst)
        writer.writerow(["Verse_ID", "Letter_Count", "Verse_Text"])
        for row in csv.DictReader(src):
            identifier, text = row["Verse_ID"], row["Verse_Text"]
            if identifier in counts:
                raise ValueError(f"Identifiant de verset dupliqué : {identifier}")
            count = 0
            for char in text:
                category = unicodedata.category(char)
                if category.startswith("M"):
                    raise ValueError(f"Signe combinant restant : {char!r}, verset {identifier}")
                if category.startswith("L") and char != "ـ":
                    if not unicodedata.name(char, "").startswith("ARABIC LETTER "):
                        raise ValueError(f"Lettre inattendue : {char!r}, verset {identifier}")
                    count += 1
                    letters[char] += 1
                else:
                    excluded[char] += 1
            counts[identifier] = count
            writer.writerow([identifier, count, text])
    return counts, letters, excluded


def compare_variation_csv(path, counts):
    """Compare seulement après le comptage indépendant, verset par verset."""
    mismatches, seen = [], set()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = [name for name in reader.fieldnames if name not in ("Verse_ID", "Verse_Text")]
        for row in reader:
            identifier = row["Verse_ID"]
            if identifier in seen:
                raise ValueError(f"Identifiant dupliqué dans les fréquences : {identifier}")
            seen.add(identifier)
            actual = sum(int(row[name]) for name in columns)
            if counts.get(identifier) != actual:
                mismatches.append({"Verse_ID": identifier, "plain_text": counts.get(identifier), "variations": actual})
    return {"rows_compared": len(seen), "mismatches": mismatches,
            "missing_verse_ids": sorted(set(counts) - seen)}


def run(directory):
    directory = Path(directory)
    source = directory / "verses.csv"
    plain = directory / "verses_without_harakat.csv"
    removed = strip_verses(source, plain)
    print(f"1. Fichier sans harakat créé : {plain} ; {sum(removed.values())} signes supprimés.")
    counts, letters, excluded = count_plain_verses(plain, directory / "verse_letter_counts.csv")
    print(f"2. Relecture et comptage : {len(counts)} versets ; {sum(letters.values())} lettres.")
    comparison = compare_variation_csv(directory / "quran_verse_variations_frequencies.csv", counts)
    report = {
        "source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "plain_text_file": str(plain), "plain_text_sha256": hashlib.sha256(plain.read_bytes()).hexdigest(),
        "method": "Delete seven harakat and shadda, no normalization. Reopen resulting CSV and count Unicode letters; exclude tatweel, spaces, digits and punctuation. Shadda does not double letters.",
        "verse_count": len(counts), "letter_total": sum(letters.values()),
        "removed_marks_total": sum(removed.values()),
        "removed_marks": {unicodedata.name(c): n for c, n in sorted(removed.items())},
        "letters": dict(sorted(letters.items())), "excluded_characters": dict(sorted(excluded.items())),
        "comparison_with_variation_csv": comparison,
    }
    (directory / "plain_text_count_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"3. Comparaison : {len(comparison['mismatches'])} écarts ; {len(comparison['missing_verse_ids'])} versets manquants.")
    if comparison["mismatches"] or comparison["missing_verse_ids"]:
        raise ValueError("Le comptage indépendant diffère du CSV des variations.")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    run(parser.parse_args().output_dir)


if __name__ == "__main__":
    main()
