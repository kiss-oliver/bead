.PHONY: test clean test2 test3

test: test2 test3

clean:
	find -name \*.pyc | xargs rm -vf --
	-find lib -type d | xargs rmdir -v --ignore-fail-on-non-empty --

test2: clean
	in-virtualenv -r test_requirements.txt nosetests

test3: clean
	in-virtualenv -p /usr/bin/python3 -r test_requirements.txt nosetests
