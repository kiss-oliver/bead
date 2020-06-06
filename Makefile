.PHONY: test clean executables

test:
	tox

executables:
	python3 build.py
