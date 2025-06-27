import nox


@nox.session
def tests_3_8(session):
    session.install("-r", "requirements.txt")
    session.install("-r", "test_requirements.txt")
    session.run("python", "--version")
    session.run("pytest", "--version")
    session.run("pytest", "--cov=.", "--cov-report=term-missing")
    session.run(
        "flake8", "bead", "bead_cli", "tests",
        "--ignore=W503,W504,E251,E241,E221,E722",
        "--max-line-length=99",
        "--exclude=.tox,.git,__pycache__,test-env,build,dist,*.pyc,*.egg-info,.cache,.eggs,./appdirs.py",
        "--max-complexity=10"
    )


@nox.session
def tests_3_12(session):
    session.install("-r", "requirements.txt")
    session.install("-r", "test_requirements.txt")
    session.run("python", "--version")
    session.run("pytest", "--version")
    session.run("pytest", "--cov=.", "--cov-report=term-missing")
    session.run(
        "flake8", "bead", "bead_cli", "tests",
        "--ignore=W503,W504,E251,E241,E221,E722",
        "--max-line-length=99",
        "--exclude=.tox,.git,__pycache__,test-env,build,dist,*.pyc,*.egg-info,.cache,.eggs,./appdirs.py",
        "--max-complexity=10"
    )
