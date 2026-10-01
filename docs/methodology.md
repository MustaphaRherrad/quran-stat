# Méthode et provenance

Le [rapport statistique complet](statistical-study.md) et ses figures sont
publiés avec le code afin de permettre une première lecture directe du dépôt.

## Corpus de référence

La présente étude porte sur le texte coranique **écrit selon l'usage courant de
la langue arabe**, tel qu'il figure dans le document source fourni. Les totaux,
les fréquences et les autres mesures sont propres à ce corpus et à sa convention
d'écriture. Le nombre de 330 705 lettres n'est donc pas présenté comme un total
indépendant de la graphie utilisée.

Une deuxième étude est envisagée sur un corpus suivant la convention du
**rasm othmani (الرسم العثماني)**. Elle sera menée séparément, avec une source
identifiée et des règles de comptage explicites adaptées à ce corpus. Elle
n'a pas encore été réalisée. Aucune comparaison entre les deux conventions
ne fait partie des résultats actuels.

`data/verses.csv` est la copie exacte de l'extraction validée du document
`quran.docx` fourni pour ce projet. Il contient 6 236 versets répartis en
114 sourates, avec les diacritiques et les numéros de verset entre parenthèses.
Il ne contient pas les métadonnées personnelles du document Word.

`data/manifest.json` conserve l'empreinte SHA-256 du CSV et du document source.
L'empreinte du CSV est testée automatiquement. Le document Word peut être
conservé dans `local/quran.docx`, hors dépôt ; un test supplémentaire vérifie
alors l'égalité exacte de son extraction avec le corpus public.

Le découpage historique, maintenu pour cette comparaison, ignore les titres
de sourates et les basmala isolées non numérotées ; il conserve les basmala
numérotées. `Verse_ID` est un indice global commençant à 1. Les références
sourate:verset sont reconstruites à partir des numéros terminaux et contrôlées.

## Lettres et harakat

Une unité comptée est une lettre suivie de tous ses signes combinants, après
normalisation Unicode NFC. La plage de lettres retenue est U+0621–U+064A,
hors tatweel U+0640. Le corpus contient 36 formes de lettres distinctes.

Les sept harakat sont fatha, damma, soukoun, kasra, dammatan, kasratan et fathatan.
La shadda est séparée et ne double pas le nombre de lettres. Le catalogue
comprend 16 catégories par lettre : lettre nue, sept harakat, shadda seule,
sept harakat avec shadda. Les 576 colonnes comprennent les fréquences nulles ;
349 formes sont effectivement observées. Cette grille n'affirme pas la validité
linguistique de toutes les combinaisons théoriques.

Les ordres canoniquement équivalents de signes sont regroupés par NFC ; aucun
signe n'est supprimé du comptage des variations. Toute autre forme observée
est ajoutée. Il n'y a aucun repli sur une forme plus courte : `أْ` n'est jamais
compté comme `أ`, et le mot `بَرَّ` compte pour deux lettres.

## Vérification indépendante

`verify_plain_text` part de l'export `verses.csv`, supprime uniquement les sept
harakat et la shadda, écrit un nouveau fichier puis le relit. Le comptage utilise
les catégories Unicode des lettres, indépendamment du catalogue de variations.
Espaces, chiffres et parenthèses sont exclus. Le résultat est **330 705 lettres**,
avec égalité verset par verset. L'extraction brute reste inchangée.

## Candidats à la prolongation

Les règles en vigueur sont :

- `ا` sans haraka, précédé dans le même mot d'une lettre portant une fatha,
  éventuellement avec shadda ; le fathatan ne remplace pas la fatha ;
- exclusion supplémentaire de l'alif de `ال` initial, `وال`, `فال` et `بال` ;
- `و` et `ي` sans les sept harakat, sans filtre sur la voyelle précédente ;
- `آ` comptée séparément.

Le filtre de l'article est nécessaire même avec la condition de fatha, notamment
dans `وَالْـ` et `فَالْـ`. Il ne constitue pas une analyse morphologique exhaustive
de tous les préfixes. Résultats : ا 24 124, و 10 034, ي 9 857, آ 1 511, soit
45 526 occurrences. Les exclusions sont documentées par mot et verset.
Ce classement graphique est distinct d'une identification phonétique du madd.

## Statistiques

Les mesures décrivent la totalité du corpus fourni : écart type de population,
quantiles linéaires, asymétrie et excès d'aplatissement. Outliers : seuils de
Tukey 1,5 × IQR, extrêmes 3 × IQR et score robuste basé sur MAD. Un outlier
n'est pas une erreur ; MAD = 0 rend le score robuste indéfini.

Les mots sont des suites de lettres arabes sans harakat. Les préfixes restent
attachés ; aucune lemmatisation ni fusion des formes de lettres. MATTR utilise
toutes les fenêtres successives, qui peuvent traverser des limites de verset
ou de sourate. Les bigrammes de mots restent dans un verset, ceux de lettres
dans un mot. La régression rang-fréquence est descriptive, sans test de loi
de puissance. Les entropies sont marginales, pas des mesures du sens du texte.

Les contrôles d'annotation issus du notebook restent des heuristiques séparées
des comptages. Leurs six signalements ne constituent pas des erreurs établies.

## Migration

La première étape a reproduit les résultats Colab, puis corrigé le catalogue
incomplet et les motifs composites. L'ancien CSV à 318 colonnes omettait
63 formes observées concernant 23 lettres. La différence de huit entre lettres
et motifs provenait du motif `بَرَّ`. Ces problèmes sont corrigés dans la méthode
actuelle. Le code de compatibilité Colab, le notebook et les exports historiques
ne sont plus nécessaires à l'exécution du projet et ont été retirés du dépôt.
