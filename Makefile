.PHONY: test test-python test-contracts test-compatibility test-web check

test: test-python test-contracts test-compatibility test-web

test-python:
	python -m pytest

test-contracts:
	npm --prefix packages/contracts test

test-compatibility:
	npm --prefix packages/compatibility test

test-web:
	npm --prefix apps/web test

check:
	python -m compileall -q pipeline tests
	$(MAKE) test
