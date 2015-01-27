.PHONY: test clean

test: clean
	tox

clean:
	git clean -fXd
	git status
