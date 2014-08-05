from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import tempfile

import fixtures

# silence warning: we are re-exporting
from testtools import TestCase
TestCase


class FileFixture(fixtures.Fixture):

    def __init__(self, content):
        self.content = content

    def setUp(self):
        super(FileFixture, self).setUp()
        fd, self.file = tempfile.mkstemp()
        os.write(fd, self.content)
        os.close(fd)
        self.addCleanup(os.remove, self.file)
