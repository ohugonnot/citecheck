"""Tests de prove_absence.py : python3 -I -m unittest discover -s tests (depuis la racine du dépôt)."""
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "citecheck", "prove_absence.py")
SOURCE = """=====[1] A
Key-value (KV) caching addresses this. The post-quantum standards are new.
=====[2] B
The electromagnetic spectrum is wide. Pipelines stall.
"""


def run(*terms, expect=None):
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "t.txt")
        open(src, "w").write(SOURCE)
        extra = ["--expect", str(expect)] if expect else []
        p = subprocess.run([sys.executable, "-I", SCRIPT, src, *extra, *terms], capture_output=True, text=True)
        return p.returncode, p.stdout


class ProveAbsence(unittest.TestCase):
    def test_suffix_and_hyphen_variants_are_found(self):
        rc, out = run("KV cache", "post quantum")
        self.assertEqual(rc, 1)
        self.assertEqual(out.count("PRESENT"), 2, out)

    def test_absence_is_proven(self):
        rc, out = run("Spectre|Meltdown", "NUMA")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.count("ABSENT"), 2)

    def test_incomplete_text_is_flagged(self):
        rc, out = run("NUMA", expect=5)
        self.assertIn("texte incomplet", out)


if __name__ == "__main__":
    unittest.main()
