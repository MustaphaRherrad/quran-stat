"""Heuristiques du notebook, conservées pour comparer la migration.

Ces signalements ne constituent pas des erreurs linguistiques établies.
"""

import re
import unicodedata
from collections import Counter

HARAKAT = "ًٌٍَُِّْ"
PREFIXES = "وفبكلت"
HURUF = ("الم", "المص", "الر", "المر", "كهيعص", "طه", "طسم", "طس", "يس", "ص", "حم", "حمعسق", "ق", "ن")
HARAKAT_NAMES = dict(zip("ًٌٍَُِّْ", ("fatha", "damma", "kasra", "sukun", "shadda", "fathatan", "dammatan", "kasratan")))
CONSONANTS = "".join(chr(n) for n in range(0x0621, 0x064B) if chr(n) not in "ايوىآ" + HARAKAT)
# Conserve notamment l'exclusion historique des consonnes suivies d'un espace.
UNANNOTATED = re.compile(f"([{CONSONANTS}])(?![{HARAKAT}\\s$])")


def previous_base(text, index):
    for position in range(index - 1, -1, -1):
        if text[position] not in HARAKAT:
            return text[position], position
    return None, -1


def is_article_lam(text, index):
    previous, position = previous_base(text, index)
    if previous not in ("ا", "ل"):
        return False
    before, _ = previous_base(text, position)
    return before is None or before.isspace() or before in PREFIXES


def find_unannotated(verses):
    findings, huruf = [], []
    for verse_id, original in enumerate(verses, 1):
        text = unicodedata.normalize("NFC", original)
        for match in UNANNOTATED.finditer(text):
            char, index = match.group(), match.start()
            if char == "ل" and is_article_lam(text, index):
                continue
            row = [verse_id, text, char, index, text[max(0, index - 10):index + 10].replace("\n", " ")]
            target = huruf if any(text.startswith(p) and index < len(p) for p in HURUF) else findings
            target.append(row)
    return findings, huruf


def inspect_letter(text, letter):
    """Analyses des fichiers ء, أ et ئ ; regarde le caractère suivant immédiat."""
    distribution = Counter()
    findings = []
    total = 0
    for index, char in enumerate(text):
        if char != letter:
            continue
        total += 1
        following = text[index + 1:index + 2]
        if following in HARAKAT_NAMES:
            distribution[HARAKAT_NAMES[following]] += 1
        if not following or following not in HARAKAT.replace("ّ", ""):
            findings.append({"index": index, "following": following, "context": text[max(0, index - 10):index + 10]})
    return {"letter": letter, "total": total, "following_harakat": dict(distribution), "without_simple_haraka": findings}
