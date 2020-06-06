.PHONY: test clean executables shiv

test:
	tox

executables:
	python3 build.py

shiv:
	shiv -o executables/bead.shiv -c bead -p '/usr/bin/python -sE' .
