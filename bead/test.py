import contextlib
import io
import os
import pathlib
import tempfile

from unittest import skip, skipIf, skipUnless

from . import tech

import tests.arglinker
from tracelog import TRACELOG


@contextlib.contextmanager
def chdir(directory):
    cwd = os.getcwd()
    try:
        os.chdir(directory)
        yield
    finally:
        os.chdir(cwd)


@contextlib.contextmanager
def setenv(variable, value):
    old_value = os.environ.get(variable)
    try:
        os.environ[variable] = value
        yield
    finally:
        if old_value is None:
            del os.environ[variable]
        else:
            os.environ[variable] = old_value


skip, skipIf, skipUnless  # reexport


class TestCase(tests.arglinker.TestCase):

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        TRACELOG(self.__class__.__module__, self.__class__.__name__)

    def tearDown(self, *args, **kwargs):
        super().tearDown(*args, **kwargs)
        TRACELOG(self.__class__.__module__, self.__class__.__name__)

    def useFixture(self, fixture):
        fixture.setUp()
        self.addCleanup(fixture.cleanUp)
        return fixture

    def new_temp_dir(self):
        return self.useFixture(TempDir()).path

    def assert_file_contains(self, filename, content_fragment):
        assert content_fragment in pathlib.Path(filename).read_text()

    def assert_file_exists(self, filename):
        assert os.path.exists(filename)

    def assert_file_does_not_exists(self, filename):
        assert not os.path.exists(filename)


class Fixture:
    def __init__(self):
        self.__cleanups = []

    def setUp(self):
        pass

    def cleanUp(self):
        while self.__cleanups:
            cleanup, args, kwargs = self.__cleanups[-1]
            cleanup(*args, **kwargs)
            del self.__cleanups[-1]

    def addCleanup(self, cleanup, *args, **kwargs):
        self.__cleanups.append((cleanup, args, kwargs))

    def useFixture(self, fixture):
        fixture.setUp()
        self.addCleanup(fixture.cleanUp)
        return fixture

    def __enter__(self):
        self.setUp()
        return self

    def __exit__(self, *_exc):
        self.cleanUp()

###
# commonly used fixtures


class TempDir(Fixture):

    def setUp(self):
        super().setUp()
        self.path = tech.fs.Path(tempfile.mkdtemp())
        # we need our own rmtree, that can remove read only files as well
        self.addCleanup(tech.fs.rmtree, self.path, ignore_errors=True)


class _CaptureStream(Fixture):

    def __init__(self, redirector):
        self.redirector = redirector
        self.string_stream = io.StringIO()
        super().__init__()

    def setUp(self):
        super().setUp()
        redirect = self.redirector(self.string_stream)
        redirect.__enter__()
        self.addCleanup(lambda: redirect.__exit__(None, None, None))

    @property
    def text(self):
        return self.string_stream.getvalue()


def CaptureStdout():
    return _CaptureStream(contextlib.redirect_stdout)


def CaptureStderr():
    return _CaptureStream(contextlib.redirect_stderr)
