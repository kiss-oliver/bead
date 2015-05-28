.PHONY: test clean

test: clean
	tox

clean:
	git clean -fXd
	rm -rf env test-env
	git status

env: clean
	virtualenv env
	. env/bin/activate; pip install -e .

test-env: clean
	virtualenv test-env
	. test-env/bin/activate; pip install -rtest_requirements.txt -rrequirements.txt
