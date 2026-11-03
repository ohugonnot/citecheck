#!/usr/bin/env python3
"""Prouve (ou réfute) qu'un livre ne dit pas X, sur le texte ENTIER et avec des variantes.

Usage :
  prove_absence.py <texte.txt> [--expect N] [--offset N] [--json] "terme|variante|variante" ["autre terme|…"]

Chaque argument est un groupe : les variantes séparées par « | » désignent la même chose
(« KV cache|key-value cache|key value cache »). Le script ajoute lui-même les variantes de
forme : pluriel simple, tiret/espace/rien (« post-quantum », « post quantum », « postquantum »),
suffixes du dernier mot (cache = caching), casse, ligatures, césures de fin de ligne et ponctuation (sous-titres automatiques).
Sortie par groupe : nombre de mentions et unités (leçons ou pages) où elles tombent.
  ABSENT (0 sur N unités)  -> l'absence est prouvée sur tout le texte
  PRESENT x fois           -> ne pas écrire « le livre ne dit pas X »
--expect N : nombre d'unités annoncées par la source (leçons du sommaire) ; si le texte en contient
moins, le script le dit en tête : une absence prouvée sur un texte incomplet ne prouve rien.
Rappel : prouver l'absence d'un MOT ne prouve pas celle de l'IDÉE ; chercher aussi les synonymes
et décrire dans le brouillon ce qui est vérifié (« 0 occurrence de … sur les 180 leçons »).
Code retour : 0 si tous les groupes sont absents, 1 si l'un est présent, 2 si usage faux.
"""
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


VC = load("verify_citations", "verify_citations.py")
CC = VC.CC


def shapes(term):
    """Variantes de forme d'un terme, déjà normalisées et sans ponctuation."""
    base = VC.loose(CC.base_normalize(term)).strip()
    words = base.split()
    out = {base, "".join(words)}
    if words:
        plural = words[:-1] + [words[-1] + ("es" if words[-1].endswith(("s", "x", "ch", "sh")) else "s")]
        out |= {" ".join(plural), "".join(plural)}
        if words[-1].endswith("s") and len(words[-1]) > 3:
            out.add(" ".join(words[:-1] + [words[-1][:-1]]))
    return out


def pattern(variant):
    """Motif d'une variante : le dernier mot tolère ses suffixes (cache = caching, caches, cached)."""
    words = variant.split()
    last = words[-1]
    root = re.sub(r"(ing|ed|es|s|e)$", "", last) if len(last) >= 5 else last
    if len(last) >= 5 and root:
        tail = re.escape(root) + r"(?:e|es|ed|ing|s)?"
    else:
        tail = re.escape(last)
    return r"(?<![a-z0-9])" + " ".join([re.escape(w) for w in words[:-1]] + [tail]) + r"(?![a-z0-9])"


def main(argv):
    flags = {a for a in argv if a in ("--json",)}
    expect, offset, rest, i = None, 0, [], 0
    while i < len(argv):
        a = argv[i]
        if a == "--expect":
            expect, i = int(argv[i + 1]), i + 1
        elif a == "--offset":
            offset, i = int(argv[i + 1]), i + 1
        elif a not in flags:
            rest.append(a)
        i += 1
    if len(rest) < 2 or not os.path.isfile(rest[0]):
        print(__doc__)
        return 2
    raw = open(rest[0], encoding="utf-8", errors="replace").read()
    units, kind = VC.split_units(raw, offset)
    hay = {n: [VC.loose(v) for v in CC.haystack_variants(t)] for n, t in units.items()}
    report, bad = [], False
    for group in rest[1:]:
        variants = {f for t in group.split("|") if t.strip() for f in shapes(t)}
        hits = {}
        for n, vs in hay.items():
            c = max(sum(len(re.findall(pattern(f), v)) for f in variants if f.strip()) for v in vs)
            if c:
                hits[n] = c
        total = sum(hits.values())
        report.append({"groupe": group, "mentions": total, "unites": sorted(hits)[:25],
                       "detail": {str(k): v for k, v in sorted(hits.items())[:25]}})
        bad |= total > 0
    short = expect is not None and len(units) < expect
    if "--json" in flags:
        print(json.dumps({"unites": len(units), "attendues": expect, "groupes": report}, ensure_ascii=False, indent=1))
    else:
        print(f"Source : {len(units)} {kind}s" + (f" sur {expect} annoncé(e)s" if expect else ""))
        if short:
            print(f"ATTENTION : texte incomplet ({len(units)} < {expect}) : aucune absence n'est prouvée tant que le reste n'est pas lu.")
        for r in report:
            if r["mentions"]:
                print(f"PRESENT {r['mentions']}x  « {r['groupe']} »  en {kind}s {r['unites']}")
            else:
                print(f"ABSENT (0 sur {len(units)} {kind}s)  « {r['groupe']} »" + ("  [texte incomplet]" if short else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
