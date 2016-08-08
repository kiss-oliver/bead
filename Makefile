.PHONY: test clean

test: clean
	tox

build: clean
	python build.py

clean:
	git clean -fXd
	rm -rf env test-env*
	git status

env: clean
	virtualenv env
	. env/bin/activate; pip install -e .

test-env: clean
	virtualenv test-env
	. test-env/bin/activate; pip install -rtest_requirements.txt -rrequirements.txt -e .

test-env2: clean
	virtualenv2 test-env2
	. test-env2/bin/activate; pip install -rtest_requirements.txt -rrequirements.txt -e .

test-env3: clean
	virtualenv3 test-env3
	. test-env3/bin/activate; pip install -rtest_requirements.txt -rrequirements.txt -e .
