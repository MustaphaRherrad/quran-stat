"""Candidats graphiques : alif après fatha, hors article ; ى final sans haraka ; waw, ya et آ séparés."""

import re
import unicodedata
from collections import Counter

from .exhaustive import HARAKAT, letter_units

ARABIC_WORD = re.compile(r"[\u0621-\u064A\u064B-\u065F\u0670]+")


def analyze_vowel_letters(text):
    """Exige une fatha précédente pour ا et exclut les préfixes d'article connus.

    Retient aussi ى sans haraka uniquement en fin de mot.

    Les harakat sont ignorées pour repérer les positions des lettres. Il s'agit
    d'une règle graphique, pas d'une analyse morphologique ou phonétique.
    """
    raw, retained = Counter(), Counter()
    exclusions = []
    for match in ARABIC_WORD.finditer(unicodedata.normalize("NFC", text)):
        word = match.group()
        units = list(letter_units(word))
        bases = "".join(unit[0] for unit in units)
        article_index, pattern = None, None
        if bases.startswith("ال"):
            article_index, pattern = 0, "ال"
        elif len(bases) >= 3 and bases[0] in "وفب" and bases[1:3] == "ال":
            article_index, pattern = 1, bases[:3]
        for index, form in enumerate(units):
            if form[0] not in "اويآى" or any(mark in HARAKAT for mark in form[1:]):
                continue
            raw[form[0]] += 1
            previous = units[index - 1] if index else ""
            reason = None
            if form[0] == "ا":
                if index == article_index:
                    reason = "article"
                elif "َ" not in previous[1:]:
                    reason = "no_preceding_fatha"
            if form[0] == "ى" and index != len(units) - 1:
                reason = "non_final_maqsoura"
            if reason:
                exclusions.append({"word": word, "pattern": pattern if reason == "article" else "",
                                   "reason": reason, "previous_unit": previous,
                                   "letter_index_in_word": index, "word_index_nfc": match.start()})
            else:
                retained[form[0]] += 1
    return raw, retained, exclusions
