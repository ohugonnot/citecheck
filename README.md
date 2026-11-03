# citecheck

**FR** · [EN below](#english)

Trois petits scripts Python (bibliothèque standard seulement) qui vérifient mécaniquement un résumé de livre écrit par un modèle : chaque citation existe-t-elle mot pour mot dans le texte du livre, à la page ou au chapitre annoncé ? Chaque chiffre y est-il ? Quand le résumé dit « le livre ne parle pas de X », est-ce vrai sur le texte entier ?

Le dépôt est né d'une chaîne d'agents qui écrit des fiches de lecture : les relecteurs trouvaient encore des citations légèrement réécrites ou rattachées à la mauvaise page. Un script les attrape pour rien, avant qu'un relecteur ne les paie en jetons.

## Lancer

```bash
python3 -I -m unittest discover -s tests    # 16 tests
./demo.sh    # le même résumé, juste (code 0), puis avec quatre fautes (code 1)
```

```bash
python3 -I citecheck/verify_citations.py résumé.md livre.txt [--offset N] [--json] [--strict-numbers]
python3 -I citecheck/prove_absence.py livre.txt [--expect N] "terme|variante" "autre terme"
python3 -I citecheck/check_claim.py livre.txt "fragment de phrase à retrouver"
```

Les messages du programme sont en français.

## Ce que chaque script contrôle

- **`verify_citations.py`** : après chaque renvoi `(lesson 3)`, `(leçon 3)`, `(p. 112)`, `(pp. 30-32)` ou `(ch. 2)`, la phrase qui précède est lue. Une citation anglaise entre guillemets doit exister mot pour mot dans l'unité citée (`ECHEC` sinon, `MAUVAISE-UNITE` si elle existe ailleurs). Un nombre introuvable est un avertissement à relire, pas un échec (il peut être calculé). Une citation française se vérifie par son original collé juste après le renvoi : `« … » (lesson 3) <!--VO: "exact English" -->`.
- **`prove_absence.py`** : « le livre ne dit pas X » se prouve sur le texte entier, avec variantes de forme (pluriel, tiret ou espace, suffixes du dernier mot, casse, ligatures, césures). Code 1 si le terme est présent. `--expect N` dit combien d'unités la source devrait avoir : un texte incomplet ne prouve rien.
- **`check_claim.py`** : le normaliseur des deux autres, utilisable seul.

Format du livre : `=====[N] titre` sépare les chapitres ou leçons ; sinon un saut de page (`\f`) sépare les pages d'un PDF (`--offset` convertit page imprimée et page PDF).

## Registre de preuves

| Affirmation | Statut | Preuve |
|---|---|---|
| Une citation altérée, un mauvais renvoi, une unité inexistante font échouer le script | Vérifié | `tests/test_e2e.py::test_bad_summary_fails_on_each_fault` |
| Le résumé juste passe | Vérifié | `tests/test_e2e.py::test_good_summary_passes` |
| Les tests rougissent si on casse la comparaison de citations | Vérifié | cinq tests passent au rouge quand `present()` répond toujours « oui » (essai du 03/11/2026, non automatisé) |
| Les tests rougissent si on casse les variantes de forme | Vérifié | `test_suffix_and_hyphen_variants_are_found` passe au rouge quand la tolérance aux suffixes des mots est retirée, ainsi que `test_absence_claims` selon la mutation (même essai) |
| Une absence prouvée sur le texte entier prouve l'absence de l'IDÉE | **Faux, non prétendu** | le script prouve l'absence d'un MOT et de ses variantes de forme, pas des synonymes : à compléter à la main |
| Une citation française sans original `<!--VO-->` est vérifiée | **Non vérifié par texte** | seul son renvoi l'est, le reste va au relecteur |
| Les chiffres écrits en lettres (« vingt ») sont retrouvés | Non vérifié | seuls les chiffres arabes le sont |
| La CI GitHub Actions passe | Vérifié | exécution 41663560664 (03/11/2026) : tests et démo verts sur Python 3.9, 3.10 et 3.12 ; seuls les systèmes Linux (ubuntu) ont été essayés |

Les extraits de `examples/book.txt` sont un texte inventé pour le dépôt, pas un livre publié.

## Licence

MIT.

---

## English

Three small stdlib-only Python scripts that mechanically check a book summary written by a model: does each quote exist word for word in the book's text, at the page or chapter it names? Is each number there? When the summary says "the book never mentions X", is that true across the whole text?

It started as part of an agent pipeline that writes reading notes. Human-style reviewers kept finding quotes that were slightly reworded or pinned to the wrong page. A script catches them for free, before a reviewer pays tokens for it.

```bash
python3 -I -m unittest discover -s tests    # 16 tests
./demo.sh    # same summary: correct (exit 0), then with four faults (exit 1)
```

- `verify_citations.py summary.md book.txt` — quotes, numbers and references (`(lesson 3)`, `(p. 112)`, `(ch. 2)`); `ECHEC` if a quote is not in the cited unit, `MAUVAISE-UNITE` if it exists elsewhere.
- `prove_absence.py book.txt "term|variant"` — proves a term is absent from the whole text, with form variants; exit code 1 if it is present.
- `check_claim.py` — the shared normalizer.

The program's messages are in French. Source format: `=====[N] title` separates chapters or lessons, otherwise a form feed (`\f`) separates PDF pages. The proof register above says what is verified and what is not; the CI (GitHub Actions, Python 3.9, 3.10 and 3.12 on Ubuntu) passed on 3 November 2026. `examples/book.txt` is invented text.

MIT license.
