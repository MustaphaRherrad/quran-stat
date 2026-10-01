"""Étude descriptive reproductible du corpus validé : python -m quran_stat.study."""

import argparse
import csv
import hashlib
import html
import os
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from openpyxl import Workbook

from .exhaustive import HARAKAT, letter_units
from .io import write_json
from .text_metrics import concentration, distribution, lexical_metrics, mattr, outlier_flags, zipf_fit
from .vowel_letters import analyze_vowel_letters

STRIP_MARKS = str.maketrans("", "", "ًٌٍَُِّْ")


def words_from_plain(text):
    """Suites de lettres arabes, sans découpage morphologique des clitiques."""
    return re.findall(r"[ء-غف-ي]+", text)


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def save_table(directory, name, rows, columns=None):
    columns = columns or list(rows[0])
    with (directory / f"{name}.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def frequency_rows(counts):
    total = sum(counts.values())
    return [{"rank": rank, "form": form, "count": count, "share": count / total}
            for rank, (form, count) in enumerate(sorted(counts.items(), key=lambda item: (-item[1], item[0])), 1)]


def vowel_letter_rows(retained):
    counts = {base: retained.get(base, 0) for base in "اويآى"}
    total = sum(counts.values())
    return [{"letter": base, "count": count, "share": count / total if total else 0}
            for base, count in counts.items()]


def plots(directory, verse_rows, surah_rows, letters, words, variations, fit, retained_vowels):
    os.environ.setdefault("MPLCONFIGDIR", str(directory / ".mplconfig"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(directory / f"{name}.png", dpi=180)
        fig.savefig(directory / f"{name}.pdf")
        plt.close(fig)

    lengths = np.array([row["letters"] for row in verse_rows])
    word_counts = np.array([row["words"] for row in verse_rows])
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes[0, 0].hist(lengths, bins="fd", color="#2563eb")
    axes[0, 0].axvline(np.median(lengths), color="#ea580c", label="Médiane")
    axes[0, 0].set(xlabel="Lettres par verset", ylabel="Nombre de versets", title="Distribution des longueurs")
    axes[0, 0].legend()
    axes[0, 1].boxplot(lengths, orientation="horizontal")
    axes[0, 1].set(xlabel="Lettres par verset", yticks=[], title="Boîte à moustaches : règle 1,5 × IQR")
    axes[1, 0].hist(word_counts, bins="fd", color="#0d9488")
    axes[1, 0].set(xlabel="Mots graphiques par verset", ylabel="Nombre de versets", title="Distribution des mots par verset")
    axes[1, 1].scatter(word_counts, lengths, s=5, alpha=0.2, rasterized=True)
    axes[1, 1].set(xlabel="Mots graphiques", ylabel="Lettres", title="Relation entre les deux longueurs")
    save(fig, "01_verse_lengths")

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    forms, values = zip(*letters.most_common())
    axes[0, 0].bar(range(len(forms)), values, color="#2563eb")
    axes[0, 0].set(xticks=range(len(forms)), xticklabels=forms, ylabel="Occurrences", title="Fréquences des 36 lettres")
    axes[0, 1].hist(list(variations.values()), bins=35, color="#0d9488")
    axes[0, 1].set(xlabel="Fréquence d'une variation observée", ylabel="Nombre de variations", title="Variations : fréquences strictement positives")
    values = np.sort(list(letters.values()))
    axes[1, 0].plot(np.linspace(0, 1, len(values) + 1), np.r_[0, np.cumsum(values) / sum(values)], label="Lettres")
    axes[1, 0].plot([0, 1], [0, 1], linestyle="--", color="gray", label="Égalité")
    axes[1, 0].set(xlabel="Part cumulée des types de lettres", ylabel="Part cumulée des occurrences", title="Concentration des fréquences")
    axes[1, 0].legend()
    marks = Counter()
    for form, count in variations.items():
        for mark in form[1:]:
            if mark in HARAKAT:
                marks[HARAKAT[mark]] += count
    axes[1, 1].bar(list(marks), list(marks.values()), color="#7c3aed")
    axes[1, 1].tick_params(axis="x", rotation=35)
    axes[1, 1].set(ylabel="Signes", title="Les sept harakat (shadda exclue)")
    save(fig, "02_letters_and_marks")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    values = np.array(sorted(words.values(), reverse=True))
    ranks = np.arange(1, len(values) + 1)
    axes[0].loglog(ranks, values, color="#2563eb", label="Observations")
    axes[0].loglog(ranks, 10 ** fit["intercept"] * ranks ** fit["slope"], linestyle="--", color="#ea580c", label="Ajustement descriptif")
    axes[0].set(xlabel="Rang du mot", ylabel="Fréquence", title="Courbe rang-fréquence du vocabulaire")
    axes[0].legend()
    histogram = Counter(words.values())
    axes[1].loglog(sorted(histogram), [histogram[n] for n in sorted(histogram)], ".", color="#0d9488")
    axes[1].set(xlabel="Nombre d'occurrences d'un mot", ylabel="Nombre de types", title="Fréquence des fréquences")
    save(fig, "03_lexical_distribution")

    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    axes[0].bar([r["surah"] for r in surah_rows], [r["letters"] for r in surah_rows], color="#2563eb")
    axes[0].set(ylabel="Total de lettres", title="Volume par sourate (ordre du corpus)")
    axes[1].plot([r["surah"] for r in surah_rows], [r["mean_letters_per_verse"] for r in surah_rows], color="#0d9488")
    axes[1].set(xlabel="Numéro de sourate", ylabel="Lettres par verset", title="Longueur moyenne des versets par sourate")
    save(fig, "04_surahs")

    vowel_rows = vowel_letter_rows(retained_vowels)
    total = sum(row["count"] for row in vowel_rows)
    fig, ax = plt.subplots(figsize=(10, 6.5))
    wedges, labels, percentages = ax.pie(
        [row["count"] for row in vowel_rows],
        labels=[row["letter"] for row in vowel_rows],
        colors=["#2563eb", "#0f766e", "#c2410c", "#7e22ce", "#a16207"],
        autopct=lambda percent: f"{percent:.2f} %".replace(".", ",") if percent >= 8 else "",
        startangle=90, counterclock=False, pctdistance=0.74,
        wedgeprops={"edgecolor": "white", "linewidth": 2},
        textprops={"fontsize": 15},
    )
    for label in percentages:
        label.set_color("white")
        label.set_fontsize(12)
        label.set_fontweight("bold")
    names = ["Alif", "Waw", "Ya", "Alif madda", "Alif maqsoura"]
    ax.legend(wedges, [f"{name} : {row['count']:,} ({100 * row['share']:.2f} %)".replace(",", " ").replace(".", ",")
                       for name, row in zip(names, vowel_rows)],
              loc="center left", bbox_to_anchor=(1, 0.5), frameon=False)
    ax.set_title("Lettres de prolongation — répartition graphique\n"
                 + f"{total:,} occurrences · alif madda inclus".replace(",", " "), pad=22)
    fig.text(0.5, 0.025, "Alif : sans haraka, après fatha dans le même mot, hors article identifié.\n"
             "Waw et ya : sans haraka ; آ séparée ; ى final sans haraka.\n"
             "Les pourcentages portent sur ces cinq catégories, pas sur toutes les lettres du corpus.",
             ha="center", fontsize=9, color="#475569")
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(directory / "05_vowel_letters_pie.png", dpi=180)
    fig.savefig(directory / "05_vowel_letters_pie.pdf")
    plt.close(fig)

    # Aperçu public régénérable avec les mêmes données que le rapport.
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes[0, 0].hist(lengths, bins="fd", color="#2563eb")
    axes[0, 0].set(title="Longueur des versets", xlabel="Lettres par verset", ylabel="Versets")
    frequent = letters.most_common(10)
    axes[0, 1].barh([x[0] for x in frequent][::-1], [x[1] for x in frequent][::-1], color="#0f766e")
    axes[0, 1].set(title="Dix lettres les plus fréquentes", xlabel="Occurrences")
    marks = {name: sum(count for form, count in variations.items() if mark in form[1:])
             for mark, name in HARAKAT.items()}
    axes[1, 0].bar(list(marks), list(marks.values()), color="#7e22ce")
    axes[1, 0].tick_params(axis="x", labelrotation=30)
    axes[1, 0].set(title="Fréquence des sept harakat", ylabel="Signes")
    axes[1, 1].barh([r["letter"] for r in vowel_rows][::-1],
                    [r["count"] for r in vowel_rows][::-1], color="#c2410c")
    for i, row in enumerate(reversed(vowel_rows)):
        axes[1, 1].text(row["count"] + 250, i,
                        f"{row['count']:,} · {row['share']:.1%}".replace(",", " "), va="center", fontsize=9)
    axes[1, 1].set(title=f"Candidats à la prolongation : {total:,}".replace(",", " "),
                    xlabel="Occurrences", xlim=(0, max(r["count"] for r in vowel_rows) * 1.4))
    fig.suptitle("Texte coranique écrit selon l’usage courant de la langue arabe\n"
                 + f"{sum(letters.values()):,} lettres · {len(verse_rows):,} versets · {len(surah_rows)} sourates".replace(",", " "))
    fig.text(0.5, 0.01, "Critères graphiques : ا après fatha, hors article ; و et ي sans haraka ; آ séparée ; ى final sans haraka.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(directory / "corpus-overview.png", dpi=180)
    fig.savefig(directory / "corpus-overview.pdf")
    plt.close(fig)


def make_report(summary, verse_rows, surah_rows, letter_rows, word_rows, output):
    d = summary["distributions"]
    lex = summary["lexical"]
    fmt = lambda value: f"{value:,.2f}".replace(",", " ").replace(".", ",")
    pct = lambda value: fmt(value * 100) + " %"
    lines = ["# Étude statistique du texte coranique — écriture arabe courante", "",
             "Cette étude porte sur le texte coranique **écrit selon l'usage courant de la langue arabe**, tel qu'il figure dans le document Word fourni. Les résultats sont propres à ce corpus et à cette convention d'écriture.",
             "Une **deuxième étude distincte selon la convention du rasm othmani (الرسم العثماني)** est envisagée par la suite. Elle n'est pas encore réalisée ; aucune comparaison avec cette convention n'est incluse dans les résultats actuels.", "",
             f"Base analysée : **{summary['verses']:,} versets, {summary['surahs']} sourates, {summary['letters']:,} lettres et {summary['words']:,} mots graphiques**.".replace(",", " "),
             "Le total de lettres est contrôlé contre les textes sans harakat et contre chaque ligne du CSV des variations.", "",
             "## 1. Méthode et portée", "",
             "Sources : `outputs/verses.csv`, `outputs/verses_without_harakat.csv` et `outputs/quran_verse_variations_frequencies.csv`. Les empreintes SHA-256 sont conservées dans `summary.json`.",
             "Les mots sont des suites de lettres arabes du texte sans harakat. Les préfixes attachés restent attachés ; aucune lemmatisation ni fusion de ا, أ, إ, آ, ة, ه, ى et ي. Ce sont des formes graphiques, pas des racines ni des lexèmes.",
             "Les lettres et leurs signes sont analysés en NFC. La shadda ne double pas le nombre de lettres. Les numéros, parenthèses et espaces sont exclus. Les sourates sont reconstruites à partir des retours à (1), avec contrôle de toute la séquence des numéros.",
             "Il s'agit de statistiques de la totalité du corpus fourni : écart type de population (ddof=0), quantiles à interpolation linéaire. Pas de tests de significativité ni d'hypothèse d'indépendance des versets. Les différences ne prouvent ni intention, ni causalité, ni singularité par rapport à d'autres corpus.", "",
             "## 2. Longueur des versets et des mots", "",
             "| Mesure | Lettres / verset | Mots / verset | Lettres / mot (occurrences) |",
             "|---|---:|---:|---:|"]
    for label, key in [("Minimum", "min"), ("Q1", "q1"), ("Médiane", "median"), ("Moyenne", "mean"), ("Q3", "q3"),
                       ("95e percentile", "p95"), ("Maximum", "max"), ("Écart type", "population_std"),
                       ("Écart interquartile", "iqr"), ("Écart absolu médian (MAD)", "mad"),
                       ("Coefficient de variation", "coefficient_variation"), ("Asymétrie", "skewness"), ("Excès d'aplatissement", "excess_kurtosis")]:
        lines.append(f"| {label} | " + " | ".join(fmt(d[name][key]) for name in ("verse_letters", "verse_words", "word_length_tokens")) + " |")
    lines += ["", "La moyenne supérieure à la médiane et l'asymétrie positive indiquent une queue vers les versets longs.",
              f"Corrélation descriptive lettres/mots par verset : Pearson r = **{fmt(summary['pearson_letters_words'])}**. Ces mesures de taille sont liées par construction ; cette corrélation n'est pas une découverte indépendante.", "",
              "## 3. Valeurs atypiques", "",
              "Règle de Tukey : valeur hors [Q1 − 1,5 × IQR ; Q3 + 1,5 × IQR]. Valeur extrême : même règle avec 3 × IQR. Vérification robuste complémentaire : |0,67449 × (x − médiane) / MAD| > 3,5. Si MAD = 0, cette dernière mesure est indéfinie.", "",
              "| Distribution | Borne basse | Borne haute | Atypiques Tukey | Extrêmes 3×IQR | Atypiques MAD |",
              "|---|---:|---:|---:|---:|---:|"]
    for name, row in summary["outlier_counts"].items():
        stats = d[name]
        mad_count = row['mad_outlier'] if row['mad_outlier'] is not None else "non défini (MAD = 0)"
        lines.append(f"| {name} | {fmt(stats['tukey_low'])} | {fmt(stats['tukey_high'])} | {row['tukey']} | {row['extreme']} | {mad_count} |")
    lines += ["", "Les seuils sont descriptifs : un verset long ou une lettre fréquente n'est pas une anomalie du texte. Les distributions discrètes et très asymétriques peuvent produire beaucoup de signalements. Les seuils négatifs n'identifient aucun cas inférieur pour des longueurs positives.", "",
              "### Dix versets les plus longs", "", "| Sourate:verset | Indice global | Lettres | Mots |", "|---|---:|---:|---:|"]
    for row in sorted(verse_rows, key=lambda r: (-r["letters"], r["verse_id"]))[:10]:
        lines.append(f"| {row['reference']} | {row['verse_id']} | {row['letters']} | {row['words']} |")
    lines += ["", "Tous les versets, leur texte et leurs signalements figurent dans `verse_metrics.csv` ; les seuls signalements sont dans `verse_outliers.csv`.", "",
              "## 4. Lettres, variations et harakat", "",
              f"Le corpus contient {len(letter_rows)} lettres distinctes et {summary['observed_variations']} variations observées sur {summary['catalog_variations']} colonnes. Les {summary['catalog_variations'] - summary['observed_variations']} colonnes nulles ne sont pas des formes rares attestées.",
              "Les statistiques et seuils des variations observées excluent les zéros ; une distribution séparée `variation_frequency_all_columns` inclut toute la grille pour expliciter l'effet de ce choix.", "",
              "| Lettre | Fréquence | Part des lettres |", "|---|---:|---:|"]
    for row in letter_rows[:12]:
        lines.append(f"| {row['form']} | {row['count']} | {pct(row['share'])} |")
    c = summary["letter_concentration"]
    lines += ["", f"Les dix lettres les plus fréquentes représentent **{pct(c['top_10_share'])}** des lettres. Gini des fréquences : **{fmt(c['gini_observed_types'])}** (0 = égalité).",
              f"Entropie marginale des lettres : **{fmt(c['entropy_bits'])} bits/lettre**, maximum à effectif de types fixé : {fmt(c['maximum_entropy_bits'])}. Nombre effectif de types (2^H) : {fmt(c['effective_types'])}.",
              "Cette entropie utilise seulement les fréquences marginales : elle ne mesure ni le sens, ni la prévisibilité contextuelle du texte.", "",
              "| Signe | Occurrences | Part des sept harakat |", "|---|---:|---:|"]
    mark_total = sum(summary["harakat_counts"].values())
    for name, count in summary["harakat_counts"].items():
        lines.append(f"| {name} | {count} | {pct(count / mark_total)} |")
    marks = summary["annotation_structure"]
    lines += ["", f"Shadda : **{marks['shadda_occurrences']}** signes, comptés séparément des sept harakat.",
              f"Lettres avec au moins une des sept harakat : **{marks['letters_with_haraka']}** ; sans ces sept harakat : **{marks['letters_without_haraka']}**. Parmi ces dernières, {marks['bare_letters']} sont sans signe et {marks['shadda_only_letters']} portent uniquement une shadda.",
              "Ces catégories ne signifient pas qu'une annotation manque : elles comprennent notamment les lettres de prolongation. Aucune correction linguistique n'est déduite de ces nombres.", ""]
    vowel_rows = summary["vowel_letters"]
    vowel_total = sum(row["count"] for row in vowel_rows)
    lines += ["### Lettres de prolongation : répartition graphique", "",
              f"Total retenu : **{vowel_total:,} occurrences**, pour ا, و et ي selon les critères ci-dessous, avec آ et ى final sans haraka séparés.".replace(",", " "),
              f"Pour ا, la lettre précédente doit porter une **fatha** dans le même mot (éventuellement avec shadda). Le fathatan ne remplace pas la fatha dans ce filtre. **{summary['excluded_article_alifs']} alifs d'article sont exclus** dans ال initial ou dans وال, فال, بال ; **{summary['excluded_alifs_by_reason'].get('no_preceding_fatha', 0)} autres alifs** sont exclus faute de fatha précédente.",
              "Le filtre de l'article reste nécessaire : dans وَالْـ et فَالْـ, une fatha précède aussi l'alif. Cette règle graphique reste limitée aux préfixes cités ; elle n'est pas une analyse morphologique exhaustive. Le critère de و et ي reste l'absence de haraka, et آ est comptée séparément. Le total général reste 330 705 lettres.",
              "L’alif maqsoura ى est retenu en fin de mot sans aucune des sept harakat sur cette lettre, sans condition sur les signes de la lettre précédente. Ainsi مُوسَى et هُدًى sont inclus : dans هُدًى, le fathatan porte sur د. Ce classement graphique ne distingue pas la pause de la liaison ; la shadda reste une dimension séparée.",
              f"Comparaison avant/après l’ajout de ى final sans haraka : {vowel_total - vowel_rows[-1]['count']:,} → {vowel_total:,} candidats (+{vowel_rows[-1]['count']:,}). Les quatre catégories précédentes et le total des lettres écrites restent inchangés.".replace(",", " "),
              "Les pourcentages sont calculés sur ce total, et non sur les 330 705 lettres. Ce critère graphique ne constitue pas une identification phonétique de chaque prolongation.", "",
              "| Lettre | Occurrences | Part du total retenu |", "|---|---:|---:|"]
    for row in vowel_rows:
        lines.append(f"| {row['letter']} | {row['count']} | {pct(row['share'])} |")
    lines += ["", "![Répartition des lettres de prolongation](05_vowel_letters_pie.png)", "",
              "## 5. Diversité lexicale et répétition", "",
              f"**{lex['tokens']} occurrences de mots**, **{lex['types_observed']} formes distinctes** sans harakat. TTR (types / occurrences) : **{pct(lex['ttr'])}**.",
              f"Hapax (formes présentes une seule fois) : **{lex['hapax_types']}**, soit {pct(lex['hapax_share_types'])} des types et {pct(lex['hapax_share_tokens'])} des occurrences. Formes présentes deux fois : {lex['dis_legomena_types']}.",
              f"MATTR : **{fmt(lex['mattr_500'])}** pour une fenêtre de 500 mots et **{fmt(lex['mattr_1000'])}** pour 1 000 mots. Calcul exact sur toutes les fenêtres successives ; elles peuvent franchir une limite de verset ou de sourate.",
              f"Yule K : **{fmt(lex['yule_k'])}**, calculé par 10 000 × (Σf² − N) / N² ; il résume la répétition des formes. Concentration des dix mots les plus fréquents : **{pct(lex['top_10_share'])}**.",
              "Le TTR diminue généralement avec la taille du texte ; il ne faut pas comparer directement les TTR de sourates très différentes en longueur. MATTR fixe la taille des fenêtres, mais reste sensible à la segmentation et à l'ordre du texte.", "",
              "| Mot sans harakat | Fréquence | Part des mots |", "|---|---:|---:|"]
    for row in word_rows[:15]:
        lines.append(f"| {row['form']} | {row['count']} | {pct(row['share'])} |")
    fit = summary["zipf_descriptive_fit"]
    lines += ["", f"Courbe rang-fréquence : pente log-log **{fmt(fit['slope'])}**, R² **{fmt(fit['r_squared'])}**, ajustée sur tous les {fit['types']} types. C'est un résumé descriptif, pas un test démontrant une loi de puissance ; les ex æquo et les hapax influencent la pente.",
              f"Répétitions exactes après suppression des harakat et des numéros : **{summary['repeated_plain_verse_types']}** textes de versets répétés, totalisant **{summary['repeated_plain_verse_occurrences']}** occurrences. Il ne s'agit pas d'une détection de paraphrases.",
              "`word_bigrams.csv` compte les paires de mots contigus à l'intérieur de chaque verset. `letter_bigrams.csv` compte les paires de lettres à l'intérieur de chaque mot. Aucune paire ne franchit les frontières indiquées ; ce sont des fréquences, pas des scores de collocation ni des liens sémantiques.", "",
              "## 6. Comparaison des sourates", "",
              "Les totaux mesurent surtout la taille de la sourate. La moyenne par verset permet une autre comparaison. `surah_metrics.csv` fournit aussi la médiane, la diversité brute et MATTR sur 100 mots (non défini si la sourate contient moins de 100 mots).", "",
              "### Dix plus grandes longueurs moyennes de verset", "",
              "| Sourate | Versets | Lettres | Lettres / verset | Mots / verset |", "|---|---:|---:|---:|---:|"]
    for row in sorted(surah_rows, key=lambda r: -r["mean_letters_per_verse"])[:10]:
        lines.append(f"| {row['surah']} | {row['verses']} | {row['letters']} | {fmt(row['mean_letters_per_verse'])} | {fmt(row['mean_words_per_verse'])} |")
    lines += ["", "L'ordre des sourates sur le graphique est celui du corpus ; il n'est pas traité comme une chronologie.", "",
              "## 7. Graphiques et fichiers", "",
              "Chaque graphique est fourni en PNG et en PDF. Le classeur `statistical_tables.xlsx` regroupe les tableaux ; les CSV restent disponibles pour poursuivre les analyses.", ""]
    for name in ("01_verse_lengths", "02_letters_and_marks", "03_lexical_distribution", "04_surahs"):
        lines.append(f"![{name}]({name}.png)\n")
    markdown = "\n".join(lines) + "\n"
    (output / "report.md").write_text(markdown, encoding="utf-8")
    # HTML autonome, sans dépendance réseau, avec images incorporées.
    import base64
    body, table_open = [], False
    for line in lines:
        if line.startswith("!["):
            image_name = line.split("](", 1)[1].split(")", 1)[0]
            encoded = base64.b64encode((output / image_name).read_bytes()).decode("ascii")
            body.append(f'<img alt="{image_name}" src="data:image/png;base64,{encoded}">')
            continue
        if line.startswith("|"):
            if re.fullmatch(r"[|:\- ]+", line):
                continue
            if not table_open:
                body.append("<table>")
                table_open = True
            body.append("<tr>" + "".join(f'<td dir="auto">{html.escape(c.strip())}</td>' for c in line.strip("|").split("|")) + "</tr>")
            continue
        if table_open:
            body.append("</table>")
            table_open = False
        escaped = html.escape(line)
        escaped = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"`(.*?)`", r"<code>\1</code>", escaped)
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            body.append(f"<h{level}>{escaped[level:].strip()}</h{level}>")
        elif line:
            body.append(f"<p>{escaped}</p>")
    document = '<!doctype html><html lang="fr"><meta charset="utf-8"><title>Étude statistique du corpus</title><style>body{font:17px/1.65 system-ui,sans-serif;max-width:1080px;margin:40px auto;padding:0 24px;color:#16243a}table{border-collapse:collapse;width:100%;margin:18px 0;font-variant-numeric:tabular-nums}td{padding:7px 12px;border-bottom:1px solid #ddd}tr:first-child{font-weight:bold;background:#eef3fa}h1,h2,h3{line-height:1.25}h2{margin-top:48px}img{width:100%;height:auto}code{background:#f2f4f7;padding:2px 4px}@media print{body{font-size:11px}h2{break-after:avoid}img,table{break-inside:avoid}}</style><body>' + "\n".join(body) + "</body></html>"
    (output / "report.html").write_text(document, encoding="utf-8")


def run(input_dir, output):
    output.mkdir(parents=True, exist_ok=True)
    sources = [input_dir / name for name in ("verses.csv", "verses_without_harakat.csv", "quran_verse_variations_frequencies.csv")]
    original, plain = map(read_rows, sources[:2])
    if len(original) != len(plain):
        raise ValueError("Les deux fichiers de versets n'ont pas la même longueur.")
    all_words, letter_counts, variation_counts = [], Counter(), Counter()
    verse_rows, per_surah = [], defaultdict(list)
    word_bigrams, letter_bigrams, repeated = Counter(), Counter(), defaultdict(list)
    surah, previous = 0, 0
    excluded_alifs = 0
    retained_vowels = Counter()
    alif_exclusions = []
    for index, (source, cleaned) in enumerate(zip(original, plain), 1):
        if source["Verse_ID"] != str(index) or cleaned["Verse_ID"] != str(index):
            raise ValueError("Les indices globaux ne sont pas continus.")
        if source["Verse_Text"].translate(STRIP_MARKS) != cleaned["Verse_Text"]:
            raise ValueError(f"Le texte sans harakat diffère au verset {index}.")
        match = re.search(r"\((\d+)\)\s*$", source["Verse_Text"])
        if not match:
            raise ValueError(f"Numéro terminal absent : {index}")
        number = int(match[1])
        if number == 1:
            surah += 1
            previous = 0
        if not surah or number != previous + 1:
            raise ValueError(f"Numérotation incohérente : {index}")
        previous = number
        words = words_from_plain(unicodedata.normalize("NFC", cleaned["Verse_Text"]))
        units = list(letter_units(source["Verse_Text"]))
        count = sum(map(len, words))
        if count != len(units):
            raise ValueError(f"La segmentation des mots perd des lettres : {index}")
        all_words.extend(words)
        letter_counts.update("".join(words))
        variation_counts.update(units)
        _, retained, exclusions = analyze_vowel_letters(source["Verse_Text"])
        retained_vowels.update(retained)
        excluded_alifs += len(exclusions)
        alif_exclusions.extend({"verse_id": index, **item} for item in exclusions)
        word_bigrams.update(" ".join(pair) for pair in zip(words, words[1:]))
        for word in words:
            letter_bigrams.update(word[i:i + 2] for i in range(len(word) - 1))
        reference = f"{surah}:{number}"
        repeated[" ".join(words)].append(reference)
        row = {"verse_id": index, "surah": surah, "verse": number, "reference": reference,
               "letters": count, "words": len(words), "unique_words": len(set(words)),
               "mean_word_length": count / len(words), "text": source["Verse_Text"]}
        verse_rows.append(row)
        per_surah[surah].append((row, words))
    if surah != 114:
        raise ValueError(f"Attendu 114 sourates, obtenu {surah}.")
    with sources[2].open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames[2:]
        totals = Counter(dict.fromkeys(columns, 0))
        rows_checked = 0
        for index, row in enumerate(reader):
            if index >= len(verse_rows) or row["Verse_ID"] != str(index + 1):
                raise ValueError("Indices du CSV des variations incohérents.")
            counts = {v: int(row[v]) for v in columns}
            if row["Verse_Text"] != original[index]["Verse_Text"] or sum(counts.values()) != verse_rows[index]["letters"]:
                raise ValueError(f"Écart dans le CSV des variations : {index + 1}")
            totals.update(counts)
            rows_checked += 1
        if rows_checked != len(verse_rows) or +totals != variation_counts:
            raise ValueError("Écart dans les fréquences de variations.")
    print(f"Sources contrôlées : {len(verse_rows)} versets, {sum(letter_counts.values())} lettres, {len(all_words)} mots.", flush=True)

    words = Counter(all_words)
    distributions = {
        "verse_letters": distribution(r["letters"] for r in verse_rows),
        "verse_words": distribution(r["words"] for r in verse_rows),
        "word_length_tokens": distribution(map(len, all_words)),
        "word_length_types": distribution(map(len, words)),
        "letter_frequency": distribution(letter_counts.values()),
        "variation_frequency_observed": distribution(variation_counts.values()),
        "variation_frequency_all_columns": distribution(totals.values()),
        "word_frequency": distribution(words.values()),
    }
    for row in verse_rows:
        for key in ("letters", "words"):
            row.update({f"{key}_{name}": value for name, value in outlier_flags(row[key], distributions[f"verse_{key}"]).items()})
    surah_rows = []
    for number, entries in per_surah.items():
        tokens = [word for _, sequence in entries for word in sequence]
        lengths = [row["letters"] for row, _ in entries]
        surah_rows.append({"surah": number, "verses": len(entries), "letters": sum(lengths),
                           "words": len(tokens), "mean_letters_per_verse": float(np.mean(lengths)),
                           "median_letters_per_verse": float(np.median(lengths)),
                           "mean_words_per_verse": len(tokens) / len(entries),
                           "unique_words": len(set(tokens)), "ttr": len(set(tokens)) / len(tokens),
                           "mattr_100": mattr(tokens, 100)})
    distributions["surah_letters"] = distribution(r["letters"] for r in surah_rows)
    distributions["surah_mean_verse_letters"] = distribution(r["mean_letters_per_verse"] for r in surah_rows)
    for row in surah_rows:
        row.update(outlier_flags(row["letters"], distributions["surah_letters"]))
    outlier_counts = {}
    for name, stats in distributions.items():
        if name not in ("verse_letters", "verse_words", "letter_frequency", "variation_frequency_observed", "word_frequency", "surah_letters"):
            continue
        values = {"verse_letters": [r["letters"] for r in verse_rows], "verse_words": [r["words"] for r in verse_rows],
                  "letter_frequency": letter_counts.values(), "variation_frequency_observed": variation_counts.values(),
                  "word_frequency": words.values(), "surah_letters": [r["letters"] for r in surah_rows]}[name]
        flags = [outlier_flags(value, stats) for value in values]
        outlier_counts[name] = {key: (sum(bool(f[key]) for f in flags) if stats["mad"] or key != "mad_outlier" else None)
                                for key in ("tukey", "extreme", "mad_outlier")}
    harakat = Counter({name: 0 for name in HARAKAT.values()})
    structure = Counter()
    for form, count in variation_counts.items():
        marks = form[1:]
        for mark in marks:
            if mark in HARAKAT:
                harakat[HARAKAT[mark]] += count
        structure["shadda_occurrences"] += count * marks.count("ّ")
        structure["letters_with_haraka" if any(mark in HARAKAT for mark in marks) else "letters_without_haraka"] += count
        structure["bare_letters"] += count if not marks else 0
        structure["shadda_only_letters"] += count if marks == "ّ" else 0
    lexical = lexical_metrics(all_words)
    fit = zipf_fit(words.values())
    summary = {"verses": len(verse_rows), "surahs": len(surah_rows), "letters": sum(letter_counts.values()),
               "words": len(all_words), "catalog_variations": len(totals), "observed_variations": len(variation_counts),
               "distributions": distributions, "outlier_counts": outlier_counts, "lexical": lexical,
               "letter_concentration": concentration(letter_counts.values()),
               "variation_concentration": concentration(variation_counts.values()),
               "harakat_counts": dict(harakat), "annotation_structure": dict(structure),
               "vowel_letters": vowel_letter_rows(retained_vowels),
               "excluded_alifs": excluded_alifs,
               "excluded_alifs_by_reason": dict(Counter(row['reason'] for row in alif_exclusions)),
               "excluded_article_alifs": sum(row['reason'] == 'article' for row in alif_exclusions),
               "excluded_article_alifs_by_pattern": dict(Counter(row['pattern'] for row in alif_exclusions if row['reason'] == 'article')),
               "zipf_descriptive_fit": fit,
               "pearson_letters_words": float(np.corrcoef([r["letters"] for r in verse_rows], [r["words"] for r in verse_rows])[0, 1]),
               "repeated_plain_verse_types": sum(len(refs) > 1 for refs in repeated.values()),
               "repeated_plain_verse_occurrences": sum(len(refs) for refs in repeated.values() if len(refs) > 1),
               "sources_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    letter_rows, word_rows = frequency_rows(letter_counts), frequency_rows(words)
    variation_rows = frequency_rows(variation_counts)
    for rows, name in ((letter_rows, "letter_frequency"), (word_rows, "word_frequency"), (variation_rows, "variation_frequency_observed")):
        for row in rows:
            row.update(outlier_flags(row["count"], distributions[name]))
    tables = {"verse_metrics": verse_rows,
              "verse_outliers": [r for r in verse_rows if r["letters_tukey"] or r["words_tukey"] or r["letters_mad_outlier"] or r["words_mad_outlier"]],
              "surah_metrics": surah_rows, "letter_frequencies": letter_rows,
              "vowel_letters": summary["vowel_letters"],
              "excluded_alifs": alif_exclusions,
              "excluded_article_alifs": [row for row in alif_exclusions if row['reason'] == 'article'],
              "variation_frequencies_observed": variation_rows, "word_frequencies": word_rows,
              "word_bigrams": frequency_rows(word_bigrams), "letter_bigrams": frequency_rows(letter_bigrams),
              "repeated_verses": [{"text": text, "count": len(refs), "references": ", ".join(refs)}
                                  for text, refs in sorted(repeated.items(), key=lambda item: -len(item[1])) if len(refs) > 1],
              "descriptive_statistics": [{"distribution": name, **stats} for name, stats in distributions.items()]}
    book = Workbook(write_only=True)
    for name, rows in tables.items():
        if not rows:
            continue
        save_table(output, name, rows)
        sheet = book.create_sheet(name[:31])
        sheet.freeze_panes = "A2"
        sheet.append(list(rows[0]))
        for row in rows:
            sheet.append(list(row.values()))
    book.save(output / "statistical_tables.xlsx")
    write_json(output / "summary.json", summary)
    plots(output, verse_rows, surah_rows, letter_counts, words, variation_counts, fit, retained_vowels)
    make_report(summary, verse_rows, surah_rows, letter_rows, word_rows, output)
    print(f"Rapport : {(output / 'report.html').resolve()}", flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/study"))
    args = parser.parse_args()
    run(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
