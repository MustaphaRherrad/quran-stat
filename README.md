# Quran Stat

Analyse reproductible des lettres, des harakat et du vocabulaire du texte
coranique **écrit selon l'usage courant de la langue arabe**. Le corpus fourni
contient **6 236 versets et 330 705 lettres**, selon les conventions détaillées
dans [la méthode](docs/methodology.md). Ce total et les statistiques décrivent
ce corpus et cette convention d'écriture ; ils ne sont pas à généraliser à
toutes les graphies du texte coranique.

Une **deuxième étude, distincte, sur le texte selon la convention du rasm
othmani (الرسم العثماني)** est envisagée par la suite. Elle n'est pas encore
réalisée ; les résultats actuels ne portent pas sur cette convention.

Le projet fonctionne localement, sans compte Google ni service externe.

## Installation et analyse

Python **3.12** est la version validée. Depuis la racine du projet :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m quran_stat --full
```

Cette commande calcule les fréquences, vérifie indépendamment le total sur le
texte sans harakat, compte les candidats à la prolongation et génère l'étude
statistique avec ses graphiques. Les résultats sont dans `outputs/` :

- `study/report.html` : rapport autonome, graphiques incorporés ;
- `study/statistical_tables.xlsx` : tableaux de l'étude ;
- `study/*.png` et `study/*.pdf` : graphiques, dont le camembert des prolongations ;
- `quran_verse_variations_frequencies.csv` : 576 colonnes de variations par verset ;
- `verses_without_harakat.csv` et `verse_letter_counts.csv` : comptage indépendant ;
- `vowel_letters_by_verse.csv` et `excluded_alifs.csv` : prolongations et exclusions.

Les résultats sont régénérables et exclus de Git. Une nouvelle exécution
remplace les fichiers de même nom dans le dossier de sortie.

```bash
# Comptage seul
.venv/bin/python -m quran_stat --no-plots

# Autre dossier de résultats
.venv/bin/python -m quran_stat --full --output-dir outputs/experience

# Document Word facultatif, conservé localement
.venv/bin/python -m quran_stat --input local/quran.docx --output-dir outputs/word

# Tests
.venv/bin/python -m unittest discover -s tests -v
```

L'installation facultative `pip install -e .` expose aussi la commande
`quran-stat`. Les chemins par défaut sont relatifs au répertoire courant.

## Structure

```text
data/
  verses.csv          Corpus texte validé, seule donnée nécessaire
  manifest.json       Provenance, empreintes et totaux de référence
docs/
  methodology.md      Règles de comptage et limites des analyses
quran_stat/           Modules Python et commandes
tests/               Tests unitaires et régressions sur le corpus
.github/workflows/    Vérifications automatisées
pyproject.toml       Métadonnées et dépendances du paquet
requirements.txt     Versions utilisées pour la validation
```

`local/`, `outputs/`, `.venv/` et les fichiers de configuration personnels ne
font pas partie du dépôt public. Le Word original peut rester dans `local/`
pour vérifier l'extraction ; les tests publics et l'étude n'en dépendent pas.

## Analyses disponibles

Distributions des longueurs, outliers IQR/MAD, fréquences des lettres et harakat,
comparaisons entre sourates, diversité lexicale (TTR, MATTR, hapax, Yule K),
entropie, concentration, rang-fréquence, répétitions et bigrammes.

Les mots sont des formes écrites sans harakat : les préfixes restent attachés,
sans lemmatisation. Les valeurs atypiques sont des observations statistiques,
pas des erreurs présumées. Le classement des prolongations suit des critères
graphiques explicites, pas une annotation phonétique complète.
