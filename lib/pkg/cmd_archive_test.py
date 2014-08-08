from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase
from . import cmd_archive as m

import zipfile

from ..path import write_file
from . import pkg_dir
from . import pkg_zip


class Test(TestCase):

    def test_structure(self):
        self.given_a_package_directory()
        self.when_archived()
        self.then_archive_contains_files_from_package_directory()

    # implementation

    __pkg_dir = None
    __SOURCE1 = b's1'
    __SOURCE2 = b's2'
    __OUTPUT1 = b'o1'
    assert __SOURCE2 != __SOURCE1

    def given_a_package_directory(self):
        self.__pkg_dir = self.new_temp_dir()
        pkg_dir.create(self.__pkg_dir)
        write_file(self.__pkg_dir / 'output/output1', self.__OUTPUT1)
        write_file(self.__pkg_dir / 'source1', self.__SOURCE1)
        write_file(self.__pkg_dir / 'source2', self.__SOURCE2)

    def when_archived(self):
        self.__zipfile = m.create(self.__pkg_dir)

    def then_archive_contains_files_from_package_directory(self):
        self.assertTrue(pkg_zip.Package(self.__zipfile).is_valid)

        z = zipfile.ZipFile(self.__zipfile)

        self.assertEquals(self.__OUTPUT1, z.read('data/output1'))
        self.assertEquals(self.__SOURCE2, z.read('code/source2'))

        files = z.namelist()
        self.assertIn('meta/pkgmeta', files)
        self.assertIn('meta/checksums', files)
