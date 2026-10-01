"""Actualise les copies publiques d'une étude déjà générée, sans publier sur GitHub."""

import argparse
import shutil
from pathlib import Path


def run(study_dir, docs_dir):
    study_dir, docs_dir = Path(study_dir), Path(docs_dir)
    assets = docs_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    report = (study_dir / "report.md").read_text(encoding="utf-8")
    report = "\n".join(
        "Source de référence : `data/verses.csv`. Les tableaux détaillés sont régénérables avec la commande complète du README ; le manifeste conserve l’empreinte du corpus."
        if line.startswith("Sources : ") else line
        for line in report.splitlines()
    ).rstrip() + "\n"
    for image in sorted(study_dir.glob("*.png")):
        shutil.copy2(image, assets / image.name)
        report = report.replace(f"]({image.name})", f"](assets/{image.name})")
    (docs_dir / "statistical-study.md").write_text(report, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-dir", type=Path, default=Path("outputs/study"))
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    args = parser.parse_args()
    run(args.study_dir, args.docs_dir)


if __name__ == "__main__":
    main()
