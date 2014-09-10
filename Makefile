.PHONY: test clean

test: clean
	tox

clean:
	find -name \*.pyc | xargs rm -f --
	-find lib -type d | xargs rmdir --ignore-fail-on-non-empty --
	git status
