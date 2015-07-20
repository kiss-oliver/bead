.PHONY: test clean

test: clean
	tox

clean:
	git clean -fXd
	rm -rf env test-env[23]
	git status

env: clean
	virtualenv env
	. env/bin/activate; pip install -e .

test-env2: clean
	virtualenv2 test-env2
	. test-env2/bin/activate; pip install -rtest_requirements.txt -rrequirements.txt -e .

test-env3: clean
	virtualenv3 test-env3
	. test-env3/bin/activate; pip install -rtest_requirements.txt -rrequirements.txt -e .
