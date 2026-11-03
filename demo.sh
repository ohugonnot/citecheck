#!/usr/bin/env bash
# Le même résumé : juste (code 0), puis avec quatre fautes (code 1), puis deux preuves d'absence.
cd "$(dirname "$0")" || exit 2
python3 -I citecheck/verify_citations.py examples/summary-good.md examples/book.txt
echo "--> code $?"
python3 -I citecheck/verify_citations.py examples/summary-bad.md examples/book.txt
echo "--> code $?"
python3 -I citecheck/prove_absence.py examples/book.txt "SIMD" "write-through|write through"
echo "--> code $?"
