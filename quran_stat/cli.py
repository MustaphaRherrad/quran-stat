"""Point d'entrée : corpus validé, comptage exact et étude reproductible."""

import argparse
import hashlib
from pathlib import Path

from .annotations import find_unannotated
from .corpus import split_verses
from .exhaustive import count_exhaustive, catalog_rows
from .io import read_paragraphs, read_verses, write_csv, write_json, write_xlsx
from .statistics import describe, plot_distribution


def run(source, output_dir, plots=True):
    source, output_dir = Path(source).resolve(), Path(output_dir).resolve()
    if output_dir == source.parent or output_dir in source.parents or source.parent in output_dir.parents:
        raise ValueError("Le dossier de sortie doit être séparé du dossier du corpus.")
    if source.suffix.lower() == ".docx":
        verses = split_verses(read_paragraphs(source))
    elif source.suffix.lower() == ".csv":
        verses = read_verses(source)
    else:
        raise ValueError("Format du corpus attendu : .csv ou .docx.")
    if not verses:
        raise ValueError("Aucun verset dans le corpus.")
    variations, frequencies, per_verse, consistency = count_exhaustive(verses)
    if not consistency["accounting_valid"]:
        raise ValueError("Le bilan des lettres comptées est incohérent.")
    findings, huruf = find_unannotated(verses)
    stats = describe(frequencies)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "variation_catalog.csv",
              ["Variation", "Base Letter", "Harakat", "Shadda", "Bare Letter", "Other Marks", "Frequency"],
              catalog_rows(variations, frequencies))
    write_csv(output_dir / "verses.csv", ["Verse_ID", "Verse_Text"], enumerate(verses, 1))
    rows = sorted(frequencies.items(), key=lambda pair: (-pair[1], pair[0]))
    write_csv(output_dir / "quran_letter_frequencies.csv", ["Letter Variation", "Frequency"], rows)
    write_xlsx(output_dir / "quran_letter_frequencies.xlsx", ["Letter Variation", "Frequency"], rows)
    write_csv(output_dir / "quran_verse_variations_frequencies.csv", ["Verse_ID", "Verse_Text", *variations],
              ([i, verse, *(counts[v] for v in variations)] for i, (verse, counts) in enumerate(zip(verses, per_verse), 1)))
    header = ["Verse Index", "Verse Text", "Unannotated Character", "Character Index", "Context"]
    write_csv(output_dir / "quran_unannotated_chars.csv", header, findings)
    write_csv(output_dir / "huruf_candidates.csv", header, huruf)
    report = {
        "method": "Exact letter + all combining marks; NFC; exhaustive seven-harakat/shadda catalog",
        "annotation_method": "Historical heuristic, NFC; independent of exact frequency counting",
        "verse_count": len(verses), "variation_count": len(variations),
        "consistency": consistency, "statistics": stats,
        "unannotated_candidates": len(findings), "huruf_candidates": len(huruf),
        "source_filename": source.name,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
    write_json(output_dir / "report.json", report)
    if plots:
        plot_distribution(frequencies, output_dir)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Analyse des lettres, harakat et statistiques du corpus.")
    parser.add_argument("--input", type=Path, default=Path("data/verses.csv"), help="Corpus CSV validé ou document Word.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--full", action="store_true", help="Vérification indépendante, prolongations et étude complète.")
    parser.add_argument("--no-plots", action="store_true", help="Désactive le graphique simple (sans --full).")
    args = parser.parse_args(argv)
    if args.full and args.no_plots:
        parser.error("--full produit les graphiques du rapport et ne se combine pas avec --no-plots.")
    try:
        report = run(args.input, args.output_dir, plots=not args.no_plots and not args.full)
        print(f"{report['verse_count']} versets ; {report['variation_count']} variations ; "
              f"{report['consistency']['base_letters']} lettres.")
        if args.full:
            from .verify_plain_text import run as verify
            from .count_vowel_letters import run as count_vowels
            from .study import run as study
            verify(args.output_dir)
            count_vowels(args.output_dir)
            study(args.output_dir, args.output_dir / "study")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Erreur : {exc}\n")
    print(f"Résultats : {args.output_dir.resolve()}")
    return 0
