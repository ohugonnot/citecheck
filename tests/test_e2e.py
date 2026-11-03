"""Bout en bout : le même résumé, juste puis avec quatre fautes, contre le même livre d'exemple."""
import os
import subprocess
import sys
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
BOOK = os.path.join(ROOT, "examples", "book.txt")


def run(script, *args):
    p = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "citecheck", script), *args],
                       capture_output=True, text=True)
    return p.returncode, p.stdout


class EndToEnd(unittest.TestCase):
    def test_good_summary_passes(self):
        rc, out = run("verify_citations.py", os.path.join(ROOT, "examples", "summary-good.md"), BOOK)
        self.assertEqual(rc, 0, out)
        self.assertIn("citations EN OK : 2", out)

    def test_bad_summary_fails_on_each_fault(self):
        rc, out = run("verify_citations.py", os.path.join(ROOT, "examples", "summary-bad.md"), BOOK)
        self.assertEqual(rc, 1, out)
        self.assertIn("introuvable « 99 to 100 percent »", out)  # citation altérée
        self.assertIn("MAUVAISE-UNITE", out)  # vraie citation, mauvais renvoi
        self.assertIn("leçon 9 n'existe pas", out)  # renvoi vers une unité absente
        self.assertIn("nombre 300 absent", out)  # chiffre inventé : avertissement, pas échec
        self.assertIn("3 échec(s), 1 nombre(s) à relire", out)

    def test_absence_claims(self):
        rc, out = run("prove_absence.py", BOOK, "SIMD")
        self.assertEqual(rc, 0, out)
        self.assertIn("ABSENT (0 sur 3 leçons)", out)
        rc, out = run("prove_absence.py", BOOK, "write-through|write through")
        self.assertEqual(rc, 1, out)
        self.assertIn("PRESENT 2x", out)

    def test_hyphen_and_suffix_variants(self):
        # le livre écrit « write-through » : « write through » (espace) le retrouve quand même
        rc, out = run("prove_absence.py", BOOK, "write through")
        self.assertEqual(rc, 1, out)


if __name__ == "__main__":
    unittest.main()
