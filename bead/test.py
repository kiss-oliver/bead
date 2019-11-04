import contextlib

import testtools
import fixtures
from unittest import skip, skipIf, skipUnless

from . import tech
import os

import arglinker
from tracelog import TRACELOG


@contextlib.contextmanager
def chdir(directory):
    cwd = os.getcwd()
    try:
        os.chdir(directory)
        yield
    finally:
        os.chdir(cwd)


skip, skipIf, skipUnless  # reexport

TestCase = arglinker.add_test_linker(testtools.TestCase)


class TestCase(TestCase):

    def setUp(self, *args, **kwargs):
        super(TestCase, self).setUp(*args, **kwargs)
        TRACELOG(self.__class__.__module__, self.__class__.__name__)

    def tearDown(self, *args, **kwargs):
        super(TestCase, self).tearDown(*args, **kwargs)
        TRACELOG(self.__class__.__module__, self.__class__.__name__)

    def new_temp_dir(self):
        return self.useFixture(TempDir()).path

###
# commonly used fixtures


class TempDir(fixtures.Fixture):

    def setUp(self):
        super(TempDir, self).setUp()
        self.path = tech.fs.Path(self.useFixture(fixtures.TempDir()).path)
        # we need our own rmtree, that can remove read only files as well
        self.addCleanup(tech.fs.rmtree, self.path, ignore_errors=True)


class _CaptureStdStream(fixtures.Fixture):

    def __init__(self, stream):
        assert stream.startswith('sys.std')
        super(_CaptureStdStream, self).__init__()
        self.stream = stream

    def setUp(self):
        super(_CaptureStdStream, self).setUp()
        stdout = self.useFixture(fixtures.StringStream(self.stream)).stream
        self.useFixture(fixtures.MonkeyPatch(self.stream, stdout))

    @property
    def text(self):
        return self.getDetails()[self.stream].as_text()


def CaptureStdout():
    return _CaptureStdStream('sys.stdout')


def CaptureStderr():
    return _CaptureStdStream('sys.stderr')
