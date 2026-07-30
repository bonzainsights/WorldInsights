.PHONY: test test-python test-contracts test-web check

test: test-python test-contracts test-web

test-python:
	python -m pytest

test-contracts:
	npm --prefix packages/contracts test

test-web:
	npm --prefix apps/web test

check:
	python -m compileall -q pipeline tests
	$(MAKE) test
