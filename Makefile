.PHONY: test clean executables shiv

test:
	tox

executables: git-info
	python3 build.py

shiv: git-info
	shiv -o executables/bead.shiv -c bead -p '/usr/bin/python -sE' .

git-info:
	./add-git-info.sh
