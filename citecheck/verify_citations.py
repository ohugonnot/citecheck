#!/usr/bin/env python3
"""Vérifie mécaniquement les citations et les chiffres d'un brouillon de fiche.

Usage :
  verify_citations.py <brouillon.md> <texte.txt> [--offset N] [--json] [--strict-numbers]

Pour chaque renvoi « (lesson 71) », « (lessons 70 and 72) », « (leçon 3) », « (p. 112) »,
« (pp. 30-32) » du brouillon, le script prend la phrase qui précède et :
  1. CITATIONS  : chaque passage entre guillemets écrit dans la langue du livre (anglais)
     doit exister mot pour mot dans l'une des leçons (ou pages) citées. Trouvé ailleurs :
     MAUVAISE-UNITE (le renvoi est faux). Introuvable : ECHEC. Les « … » et [...] découpent
     la citation en fragments, chacun doit exister.
  2. CHIFFRES   : chaque nombre de la phrase (hors renvois) doit apparaître dans l'unité citée,
     avec les variantes 0,25 / 0.25, 10 496 / 10,496 / 10496, « 95 to 97 » / « 95-97 ».
     Un nombre introuvable est un AVERTISSEMENT (il peut être calculé ou écrit en lettres) :
     il va à la liste de relecture, il ne fait pas échouer le script (sauf --strict-numbers).
  3. RENVOIS    : une unité citée qui n'existe pas dans la source est une ECHEC.
Les citations en français (traductions) ne sont pas vérifiables par texte : elles sont comptées
et laissées au relecteur, avec leur renvoi vérifié. Pour qu'une citation traduite le soit aussi, le
brouillon FR met l'original juste après le renvoi : « … » (leçon 71) <!--VO: "exact English" -->.
Le commentaire est vérifié comme une citation anglaise ; md2php.py le retire de la page.

Texte source : « =====[N] titre » sépare les leçons (extraits ExpertEdge) ; sinon les sauts de
page \\f séparent les pages d'un PDF (--offset décale : page PDF = page du livre + offset).
Code retour : 0 si aucune ECHEC, 1 sinon, 2 si usage faux.
Sans dépendance : bibliothèque standard seulement. La normalisation vient de check_claim.py.
"""
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load_normalizer():
    spec = importlib.util.spec_from_file_location("check_claim", os.path.join(HERE, "check_claim.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CC = load_normalizer()

# ---------- source ----------

def split_units(raw, offset=0):
    """{numéro: texte brut} ; leçons si « =====[N] », sinon pages (\\f)."""
    marks = list(re.finditer(r"^=====\[(\d+)\][^\n]*$", raw, re.M))
    if marks:
        out = {}
        for i, m in enumerate(marks):
            end = marks[i + 1].start() if i + 1 < len(marks) else len(raw)
            out[int(m.group(1))] = raw[m.end():end]
        return out, "leçon"
    pages = raw.split("\f")
    return {i + 1 - offset: p for i, p in enumerate(pages)}, "page"


def prep(text):
    return CC.haystack_variants(text)


def loose(s):
    """Sans ponctuation ni tirets : « post quantum » = « post-quantum » (sous-titres automatiques)."""
    return " " + re.sub(r"[\W_]+", " ", s).strip() + " "


def present(frag, variants, mode="strict"):
    f = CC.base_normalize(frag).strip()
    if not f:
        return True
    if mode == "loose":
        lf = loose(f)
        return any(lf in loose(v) for v in variants)
    for v in variants:
        if f in v:
            return True
    # les rips mangent parfois la pollution d'interface : un second essai sans elle
    f2 = CC.scrub_pollution(f).strip()
    if any(f2 and f2 in CC.scrub_pollution(v) for v in variants):
        return True
    # l'extraction PDF écrase les exposants (« 2^32 » devient « 232 ») : on rétablit l'exposant dans la fiche, pas dans la source
    f3 = re.sub(r"(?<=\d)\^(?=\d)", "", f2)
    return f3 != f2 and any(f3 in CC.scrub_pollution(v) for v in variants)


# ---------- brouillon ----------

REF = re.compile(
    r"\(\s*(?:lessons?|leçons?|pages?|pp?\.|ch\.|chapters?|chapitres?)\s*"
    r"(\d+(?:\s*(?:[-–—]|à|to)\s*\d+)?(?:\s*(?:,|and|et|&)\s*\d+(?:\s*(?:[-–—]|à|to)\s*\d+)?)*)"
    r"[^)]*\)", re.I)
VO = re.compile(r"(\([^()]*\))\s*<!--\s*VO\s*:\s*(.*?)\s*-->")
QUOTE = re.compile(r"«\s*([^»]+?)\s*»|“([^”]+?)”|\"([^\"\n]+?)\"")
NUM = re.compile(r"(?<![\w.])\d[\d  ,.]*\d(?:\s?%)?|(?<![\w.])\d(?![\w])")
EN_WORDS = {"the", "of", "to", "and", "is", "are", "that", "in", "it", "for", "with", "this", "be", "as", "on",
            "can", "each", "which", "by", "from", "at", "an", "or", "not", "its", "than", "more", "most"}
FR_WORDS = {"le", "la", "les", "des", "est", "un", "une", "du", "et", "que", "qui", "dans", "pour", "pas",
            "sur", "au", "aux", "ce", "ses", "son", "leur", "plus", "avec", "sont", "ne", "se"}


def refs_numbers(s):
    nums = []
    for part in re.split(r"\s*(?:,|and|et|&)\s*", s):
        m = re.match(r"(\d+)\s*(?:[-–—]|à|to)\s*(\d+)$", part.strip())
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            nums += list(range(a, b + 1)) if 0 <= b - a <= 30 else [a, b]
        elif part.strip().isdigit():
            nums.append(int(part.strip()))
    return nums


def quote_is_english(q):
    words = re.findall(r"[a-zà-ÿ']+", q.lower())
    en = sum(w in EN_WORDS for w in words)
    fr = sum(w in FR_WORDS for w in words)
    if any(ch in q for ch in "éèêàçùœâîôû"):
        fr += 2
    return en > fr or (en >= 1 and fr == 0)


def fragments(q):
    parts = re.split(r"\s*(?:…|\.\.\.|\[\s*(?:\.\.\.|…)\s*\])\s*", q)
    parts = [p.strip(" ,;:.") for p in parts]
    return [p for p in parts if len(p) >= 8 and len(p.split()) >= 2 and re.match(r"\w", p)]


def sentences_with_refs(md):
    """(ligne, renvoi, [numéros], texte) : le texte est tout ce qui précède le renvoi depuis le renvoi
    précédent de la même ligne (un paragraphe par ligne). Un reste sans renvoi est rendu avec renvoi None."""
    out = []
    for ln, line in enumerate(md.split("\n"), 1):
        # Brouillon FR : l'original anglais d'une citation traduite suit le renvoi dans un commentaire
        # « (leçon 71) <!--VO: "…" --> » ; on le ramène avant le renvoi pour qu'il soit vérifié comme une citation EN.
        line = VO.sub(lambda m: " " + m.group(2) + " " + m.group(1), line)
        pos = 0
        for m in REF.finditer(line):
            out.append((ln, m.group(0), refs_numbers(m.group(1)), line[pos:m.start()]))
            pos = m.end()
        if pos and line[pos:].strip():
            out.append((ln, None, [], line[pos:]))
        elif not pos and line.strip():
            out.append((ln, None, [], line))
    return out


def number_forms(tok):
    t = tok.replace(" ", " ").replace("\xa0", " ").strip().rstrip("%").strip()
    digits = re.sub(r"[\s]", "", t)
    forms = {digits, digits.replace(",", "."), digits.replace(".", ",")}
    if re.fullmatch(r"\d{1,3}([ ,.]\d{3})+", t):                  # séparateurs de milliers
        plain = re.sub(r"[ ,.]", "", t)
        forms |= {plain, re.sub(r"(?<=\d)(?=(\d{3})+$)", ",", plain), re.sub(r"(?<=\d)(?=(\d{3})+$)", " ", plain)}
    return forms


def number_present(tok, text_norm):
    for f in number_forms(tok):
        if re.search(r"(?<![\d.,])" + re.escape(f) + r"(?![\d]|[.,]\d)", text_norm):
            return True
    return False


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    flags = {a for a in argv if a.startswith("--") and not a.startswith("--offset")}
    offset = 0
    for i, a in enumerate(argv):
        if a == "--offset" and i + 1 < len(argv):
            offset = int(argv[i + 1])
            args = [x for x in args if x != argv[i + 1]]
    if len(args) != 2 or not all(os.path.isfile(a) for a in args):
        print(__doc__)
        return 2
    md = open(args[0], encoding="utf-8").read()
    raw = open(args[1], encoding="utf-8", errors="replace").read()
    units, kind = split_units(raw, offset)
    cache = {}

    def variants(n):
        if n not in cache:
            cache[n] = prep(units[n])
        return cache[n]

    whole = None
    results = {"quotes_ok": 0, "quotes_fail": [], "quotes_wrong_unit": [], "quotes_fr": 0, "quotes_orphan": [], "quotes_norefs": [], "quotes_loose": [],
               "refs_bad": [], "numbers_ok": 0, "numbers_warn": []}
    for ln, ref, nums, sent in sentences_with_refs(md):
        if ref is None:
            for qm in QUOTE.finditer(sent):
                q = next(g for g in qm.groups() if g)
                if not quote_is_english(q) or len(q) < 25:
                    continue
                if whole is None:
                    whole = CC.haystack_variants(raw)
                for frag in fragments(q):
                    if not present(frag, whole) and not present(frag, whole, "loose"):
                        results["quotes_orphan"].append({"ligne": ln, "citation": frag})
                    elif len(frag) >= 25:
                        results["quotes_norefs"].append({"ligne": ln, "citation": frag})
            continue
        bad = [n for n in nums if n not in units]
        for n in bad:
            results["refs_bad"].append({"ligne": ln, "renvoi": ref, "unite": n})
        nums = [n for n in nums if n in units]
        if not nums:
            continue
        # --- citations
        quote_spans = []
        for qm in QUOTE.finditer(sent):
            q = next(g for g in qm.groups() if g)
            quote_spans.append(qm.span())
            if not quote_is_english(q):
                results["quotes_fr"] += 1
                continue
            for frag in fragments(q):
                if any(present(frag, variants(n)) for n in nums):
                    results["quotes_ok"] += 1
                    continue
                if any(present(frag, variants(n), "loose") for n in nums):
                    results["quotes_ok"] += 1
                    results["quotes_loose"].append({"ligne": ln, "citation": frag})
                    continue
                if whole is None:
                    whole = CC.haystack_variants(raw)
                where = [n for n in units if present(frag, variants(n))] if present(frag, whole) else []
                entry = {"ligne": ln, "renvoi": ref, "citation": frag, "trouvee_en": where[:5]}
                (results["quotes_wrong_unit"] if where else results["quotes_fail"]).append(entry)
        # --- chiffres (hors citations et hors renvois)
        rest = sent
        for a, b in reversed(quote_spans):
            rest = rest[:a] + " " + rest[b:]
        rest = REF.sub(" ", rest)
        rest = re.sub(r"\bhttps?://\S+|`[^`]*`|\bid=\"[^\"]*\"", " ", rest)
        pool = " ".join(CC.base_normalize(units[n]) for n in nums)
        for tm in NUM.finditer(rest):
            tok = tm.group(0).strip()
            if re.fullmatch(r"\d", tok) or re.fullmatch(r"(19|20)\d\d", tok):    # chiffres isolés, années
                continue
            if number_present(tok, pool):
                results["numbers_ok"] += 1
            else:
                results["numbers_warn"].append({"ligne": ln, "renvoi": ref, "nombre": tok,
                                                "contexte": rest.strip()[-110:]})

    fails = results["quotes_fail"] + results["quotes_wrong_unit"] + results["refs_bad"]
    if "--json" in flags:
        print(json.dumps(results, ensure_ascii=False, indent=1))
    else:
        print(f"Source : {len(units)} {kind}s | citations EN OK : {results['quotes_ok']} | "
              f"citations FR non vérifiables par texte : {results['quotes_fr']} | chiffres retrouvés : {results['numbers_ok']}")
        if results["quotes_loose"]:
            print(f"  dont {len(results['quotes_loose'])} trouvée(s) seulement à la ponctuation près (sous-titres automatiques ?)")
        if results["quotes_norefs"]:
            print(f"  {len(results['quotes_norefs'])} citation(s) EN trouvée(s) dans le livre mais sans renvoi de leçon à leur suite (lignes "
                  + ", ".join(str(e['ligne']) for e in results['quotes_norefs'][:12]) + ")")
        for e in results["quotes_orphan"]:
            print(f"a-verifier l.{e['ligne']} (sans renvoi) : « {e['citation'][:90]} » n'est pas dans le livre (paraphrase, légende de schéma ou citation fausse ?)")
        for e in results["refs_bad"]:
            print(f"ECHEC  l.{e['ligne']} {e['renvoi']} : {kind} {e['unite']} n'existe pas dans la source")
        for e in results["quotes_fail"]:
            print(f"ECHEC  l.{e['ligne']} {e['renvoi']} : introuvable « {e['citation'][:100]} »")
        for e in results["quotes_wrong_unit"]:
            print(f"MAUVAISE-UNITE l.{e['ligne']} {e['renvoi']} : « {e['citation'][:80]} » est en {kind} {e['trouvee_en']}")
        for e in results["numbers_warn"]:
            print(f"a-verifier l.{e['ligne']} {e['renvoi']} : nombre {e['nombre']} absent de l'unité citée | …{e['contexte']}")
        print("RESULTAT :", "ECHEC" if fails else "OK",
              f"({len(fails)} échec(s), {len(results['numbers_warn'])} nombre(s) à relire)")
    if "--strict-numbers" in flags and results["numbers_warn"]:
        return 1
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
