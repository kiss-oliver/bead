from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import testtools
import fixtures

from . import tech
import os
import tempfile
import glued


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


TestCase = glued.glue_test_methods(testtools.TestCase)


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
