from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import testtools
import fixtures

from . import tech

Path = tech.path.Path
rmtree = tech.path.rmtree


class TestCase(testtools.TestCase):

    def new_temp_dir(self):
        path = Path(self.useFixture(fixtures.TempDir()).path)
        self.addCleanup(rmtree, path, ignore_errors=True)
        return path
