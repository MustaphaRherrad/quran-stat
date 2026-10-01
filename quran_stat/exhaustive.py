"""Comptage exact : une lettre et tous ses signes combinants forment une unité."""

import unicodedata
from collections import Counter

from .corpus import count_base_letters, is_base_letter

HARAKAT = {"َ": "fatha", "ُ": "damma", "ْ": "soukoun", "ِ": "kasra",
           "ٌ": "dammatan", "ٍ": "kasratan", "ً": "fathatan"}
SHADDA = "ّ"
BASE_LETTERS = "ءآأؤإئابتثجحخدذرزسشصضطظعغفقكلمنهويىة"


def normalize(text):
    return unicodedata.normalize("NFC", text)


def letter_units(text):
    """NFC unifie l'ordre des signes sans supprimer aucun diacritique.

    Un signe supplémentaire appartient à l'unité ; aucune correspondance
    partielle ne permet de reclasser une lettre vocalisée comme lettre nue.
    """
    text = normalize(text)
    index = 0
    while index < len(text):
        if is_base_letter(text[index]):
            end = index + 1
            while end < len(text) and unicodedata.category(text[end]).startswith("M"):
                end += 1
            yield text[index:end]
            index = end
        else:
            index += 1


def build_catalog(observed=()):
    """16 catégories par lettre, plus toute autre forme effectivement observée.

    Les combinaisons théoriques sont incluses même à zéro : cette grille
    n'affirme pas leur validité linguistique (ex. shadda + soukoun).
    """
    observed = {normalize(v) for v in observed}
    bases = set(BASE_LETTERS) | {v[0] for v in observed}
    return sorted(observed | {
        normalize(base + vowel + shadda)
        for base in bases for vowel in ("", *HARAKAT) for shadda in ("", SHADDA)
    })


def count_exhaustive(verses):
    per_verse = [Counter(letter_units(verse)) for verse in verses]
    observed = Counter()
    for counts in per_verse:
        observed.update(counts)
    catalog = build_catalog(observed)
    frequencies = Counter({v: observed[v] for v in catalog})
    letters = sum(count_base_letters(normalize(verse)) for verse in verses)
    return catalog, frequencies, per_verse, {
        "base_letters": letters, "counted_units": sum(frequencies.values()),
        "difference": letters - sum(frequencies.values()),
        "composite_contributions": {}, "unmatched_letters": {},
        "accounting_valid": all(sum(counts.values()) == count_base_letters(normalize(verse))
                                for verse, counts in zip(verses, per_verse)),
    }


def catalog_rows(catalog, frequencies):
    for variation in catalog:
        marks = variation[1:]
        yield [variation, variation[0],
               ", ".join(name for mark, name in HARAKAT.items() if mark in marks),
               SHADDA in marks, not marks,
               "".join(mark for mark in marks if mark not in HARAKAT and mark != SHADDA),
               frequencies[variation]]
