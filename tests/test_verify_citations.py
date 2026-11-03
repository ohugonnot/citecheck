"""Tests de verify_citations.py : python3 -I -m unittest discover -s tests (depuis la racine du dépôt)."""
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "citecheck", "verify_citations.py")
SOURCE = """=====[1] Intro
Caches work because programs repeat themselves. Hit rates are "95 to 97 percent" in practice.
=====[2] Pipeline
The processor reaches an IPC of 0.25 on this loop, and 10,496 cores run in parallel.
"""


def run(draft):
    with tempfile.TemporaryDirectory() as d:
        src, md = os.path.join(d, "t.txt"), os.path.join(d, "d.md")
        open(src, "w").write(SOURCE)
        open(md, "w").write(draft)
        p = subprocess.run([sys.executable, "-I", SCRIPT, md, src], capture_output=True, text=True)
        return p.returncode, p.stdout


class VerifyCitations(unittest.TestCase):
    def test_good_quote_and_numbers(self):
        rc, out = run('He says "95 to 97 percent" of accesses hit (lesson 1). An IPC of 0.25 and 10 496 cores (lesson 2).\n')
        self.assertEqual(rc, 0, out)
        self.assertNotIn("a-verifier", out)

    def test_exponent_flattened_by_extraction(self):
        # la source (extraction PDF) a perdu l'exposant ; la fiche l'écrit 2^32
        global SOURCE
        old = SOURCE
        SOURCE = old + "=====[3] Birthday\nExpect a repetition after approximately 232 nonces in practice.\n"
        try:
            rc, out = run('Il écrit "repetition after approximately 2^32 nonces" (lesson 3).\n')
        finally:
            SOURCE = old
        self.assertEqual(rc, 0, out)

    def test_chapter_reference(self):
        # livres sans folios (version HTML) : « (ch. 2) » vaut « (leçon 2) »
        rc, out = run('He says "95 to 97 percent" of accesses hit (ch. 1).\n')
        self.assertEqual(rc, 0, out)
        self.assertIn("citations EN OK : 1", out)
        rc, out = run('He says "95 to 97 percent" of accesses hit (ch. 2).\n')
        self.assertEqual(rc, 1, out)

    def test_altered_quote(self):
        rc, out = run('He says "95 to 99 percent" of accesses hit (lesson 1).\n')
        self.assertEqual(rc, 1)
        self.assertIn("introuvable", out)

    def test_wrong_lesson(self):
        rc, out = run('He says "95 to 97 percent" of accesses hit (lesson 2).\n')
        self.assertEqual(rc, 1)
        self.assertIn("MAUVAISE-UNITE", out)

    def test_missing_lesson(self):
        rc, out = run('See "95 to 97 percent" here (lessons 1 and 9).\n')
        self.assertEqual(rc, 1)
        self.assertIn("n'existe pas", out)

    def test_number_is_a_warning_not_a_failure(self):
        rc, out = run("Un IPC de 0,35 sur cette boucle (leçon 2).\n")
        self.assertEqual(rc, 0)
        self.assertIn("a-verifier", out)

    def test_french_quote_is_counted_not_checked(self):
        rc, out = run("Il parle de « la plupart du temps à attendre » (leçon 1).\n")
        self.assertEqual(rc, 0)
        self.assertIn("citations FR non vérifiables par texte : 1", out)

    def test_vo_comment_checks_a_french_quote(self):
        rc, out = run('Il parle de « 95 à 97 pour cent » (leçon 1) <!--VO: "95 to 97 percent" -->.\n')
        self.assertEqual(rc, 0, out)
        self.assertIn("citations EN OK : 1", out)
        rc, out = run('Il parle de « 95 à 99 pour cent » (leçon 1) <!--VO: "95 to 99 percent" -->.\n')
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
