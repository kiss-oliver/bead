.PHONY: test clean executables

test: clean
	tox

executables: clean
	python3 build.py

clean:
	# remove all files ignored by git, recurse into directories, keeps manually created, not ignored files
	git clean -fXd
	git status
