.PHONY: test check

test:
	python -m pytest

check:
	python -m compileall -q pipeline tests
	python -m pytest
