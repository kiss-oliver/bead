from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import testtools
import fixtures

from .path import Path


class TestCase(testtools.TestCase):

    def new_temp_dir(self):
        return Path(self.useFixture(fixtures.TempDir()).path)
