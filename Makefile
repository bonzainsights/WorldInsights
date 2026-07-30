.PHONY: test test-python test-contracts check

test: test-python test-contracts

test-python:
	python -m pytest

test-contracts:
	npm --prefix packages/contracts test

check:
	python -m compileall -q pipeline tests
	$(MAKE) test
