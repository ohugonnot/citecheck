#!/usr/bin/env python3
"""Vérification adversariale d'une claim contre le texte extrait d'un livre.

Usage :
  check_claim.py <texte.txt> [<texte2.txt> ...] "fragment un" ["fragment deux" ...]
  (tout argument qui est un fichier existant est traité comme texte source,
   le reste comme fragments à chercher)

Normalise texte ET fragments avant de chercher, pour neutraliser les artefacts
de rip : césures de fin de ligne, soft hyphens U+00AD, ligatures ﬁ/ﬂ/ﬀ/ﬃ/ﬄ,
sauts de page \f (y compris au milieu d'une citation), apostrophes et
guillemets typographiques, '' pour ", espaces insécables, casse.
Si un fragment reste introuvable, re-essaie après épuration de la pollution
d'interface connue (WOW! eBook, menus Safari) et le signale.

Un FAIL reste une PRÉSOMPTION, pas une preuve d'invention : re-tester avec un
fragment plus court, sans mots composés et sans mots à Th/fi (certains rips
suppriment ces glyphes : « ere are » = « There are »).

Code retour : 0 si tous les fragments sont trouvés, 1 sinon.
"""
import os
import re
import sys

LIGATURES = {
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl",
    "ﬃ": "ffi", "ﬄ": "ffl",
}

POLLUTION = [
    "wow! ebook", "www.wowebook.org",
    "history", "topics", "tutorials", "offers & deals", "highlights",
    "settings", "support", "sign out", "playlists",
]


def base_normalize(s):
    for k, v in LIGATURES.items():
        s = s.replace(k, v)
    s = s.replace("­", "")                     # soft hyphen
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("''", '"')                        # guillemets fermants doublés
    s = s.replace(" ", " ")
    s = re.sub(r"[\f\n\r\t]", " ", s)
    s = re.sub(r" {2,}", " ", s)
    return s.lower()


def haystack_variants(raw):
    """Deux lectures de la césure : recollée sans tiret, recollée avec tiret."""
    glued = re.sub(r"(\w)-[ \t]*\n[ \t]*(\w)", r"\1\2", raw)
    hyphen = re.sub(r"(\w)-[ \t]*\n[ \t]*(\w)", r"\1-\2", raw)
    return [base_normalize(glued), base_normalize(hyphen)]


def scrub_pollution(s):
    for w in POLLUTION:
        s = re.sub(r"\b" + re.escape(w) + r"\b", " ", s)
    return re.sub(r" {2,}", " ", s)


def find(frag_norm, variants):
    for v in variants:
        i = v.find(frag_norm)
        if i >= 0:
            return v[max(0, i - 90):i + len(frag_norm) + 90]
    return None


def main(argv):
    files, frags = [], []
    for a in argv:
        (files if os.path.isfile(a) else frags).append(a)
    if not files or not frags:
        print(__doc__)
        return 2

    texts = []
    for f in files:
        raw = open(f, encoding="utf-8", errors="replace").read()
        texts.append((f, haystack_variants(raw)))

    all_ok = True
    for frag in frags:
        frag_norm = base_normalize(frag).strip()
        hit = None
        for fname, variants in texts:
            ctx = find(frag_norm, variants)
            if ctx:
                hit = (fname, ctx, "")
                break
            ctx = find(frag_norm, [scrub_pollution(v) for v in variants])
            if ctx:
                hit = (fname, ctx, " (après épuration pollution rip)")
                break
        if hit:
            fname, ctx, note = hit
            print(f"OK   « {frag} »{note}  [{fname}]")
            print(f"     …{ctx}…")
        else:
            all_ok = False
            print(f"FAIL « {frag} »")
            print("     présomption seulement : re-tester un fragment plus court,")
            print("     sans mots composés ni mots à Th/fi.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
