from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import testtools
import fixtures

from . import tech


class TestCase(testtools.TestCase):

    def new_temp_dir(self):
        path = tech.fs.Path(self.useFixture(fixtures.TempDir()).path)
        # we need our own rmtree, that can remove read only files as well
        self.addCleanup(tech.fs.rmtree, path, ignore_errors=True)
        return path

    def new_temp_home_dir(self):
        path = tech.fs.Path(self.useFixture(fixtures.TempHomeDir()).path)
        self.addCleanup(tech.fs.rmtree, path, ignore_errors=True)
        return path
