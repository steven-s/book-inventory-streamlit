.PHONY: test test-quiet coverage

test:
	conda run -n book-inventory pytest

test-quiet:
	conda run -n book-inventory pytest -q

coverage: test
