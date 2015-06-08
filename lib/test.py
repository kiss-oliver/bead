from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import functools
import testtools
import fixtures

from . import tech
import os
import tempfile
import arglinker


def xfail(test, why=""):
    """testtools' version of unittest's expectedFailure decorator

    The one from unittest does not work with testtools.TestCase!
    """
    @functools.wraps(test)
    def expect_to_fail(self):
        def errors_to_failure(f):
            # convert all exceptions including SystemExit
            # and other heavy ones to failure
            try:
                f(self)
            except BaseException as e:
                self.fail(e)
        self.expectFailure(
            why,
            errors_to_failure, arglinker.func_with_fixture_resolver(test)
        )
    return expect_to_fail


class TempDir(fixtures.Fixture):

    def setUp(self):
        super(TempDir, self).setUp()
        self.path = tech.fs.Path(self.useFixture(fixtures.TempDir()).path)
        # we need our own rmtree, that can remove read only files as well
        self.addCleanup(tech.fs.rmtree, self.path, ignore_errors=True)


class TempHomeDir(fixtures.Fixture):

    def setUp(self):
        super(TempHomeDir, self).setUp()
        self.path = tech.fs.Path(self.useFixture(fixtures.TempHomeDir()).path)
        # we need our own rmtree, that can remove read only files as well
        self.addCleanup(tech.fs.rmtree, self.path, ignore_errors=True)


TestCase = arglinker.add_test_linker(testtools.TestCase)


class TestCase(TestCase):

    def new_temp_dir(self):
        return self.useFixture(TempDir()).path

    def new_temp_home_dir(self):
        return self.useFixture(TempHomeDir()).path

    def new_temp_filename(self):
        fd, name = tempfile.mkstemp()
        os.close(fd)
        os.unlink(name)
        self.addCleanup(os.unlink, name)
        return name
