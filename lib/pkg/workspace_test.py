from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase
from . import workspace as m


class Test(TestCase):

    def test(self):
        self.given_an_empty_directory()
        self.when_initialized()
        self.then_directory_is_a_valid_pkg_dir()

    # implementation

    __pkg_dir = None

    def given_an_empty_directory(self):
        self.__pkg_dir = self.new_temp_dir()

    def when_initialized(self):
        m.Workspace(self.__pkg_dir).create()

    def then_directory_is_a_valid_pkg_dir(self):
        self.assertTrue(m.Workspace(self.__pkg_dir).is_valid)
