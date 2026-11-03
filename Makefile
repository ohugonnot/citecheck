.PHONY: test demo e2e
test:
	python3 -I -m unittest discover -s tests -v

# le même résumé : juste (code 0), puis avec quatre fautes (code 1)
demo:
	python3 -I citecheck/verify_citations.py examples/summary-good.md examples/book.txt
	-python3 -I citecheck/verify_citations.py examples/summary-bad.md examples/book.txt
	-python3 -I citecheck/prove_absence.py examples/book.txt "SIMD" "write-through|write through"

e2e: test
