"""Découpage historique du document, sans normalisation des comptages."""

import re

BASMALA = "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ"


def split_verses(paragraphs):
    """Reproduit la cellule 4 ; les numéros entre parenthèses sont conservés.

    Les identifiants des exports sont des indices globaux (base 1), pas des
    couples sourate/verset. Un reliquat de paragraphe rejoint le verset précédent.
    """
    verses = []
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph or paragraph == BASMALA:
            continue
        if "سورة" in paragraph and not re.search(r"\(\d+\)", paragraph):
            continue
        current = ""
        for part in re.split(r"(\s*\(\d+\)\s*)", paragraph):
            part = part.strip()
            if not part:
                continue
            if re.fullmatch(r"\(\d+\)", part):
                if current:
                    verses.append(current + " " + part)
                    current = ""
            else:
                current += (" " if current else "") + part
        if current:
            if verses:
                verses[-1] += " " + current
            else:
                verses.append(current)
    return verses


def is_base_letter(char):
    """Plage historique U+0621–U+064A, hors tatweel U+0640."""
    return "\u0621" <= char <= "\u064a" and char != "\u0640"


def count_base_letters(text):
    return sum(is_base_letter(char) for char in text)
