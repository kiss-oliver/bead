from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import fixtures
from ..test import TestCase, FileFixture
from . import cmd_archive as m

import os
import zipfile

from ..path import Path, write_file
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
        self.__pkg_dir = Path(self.useFixture(fixtures.TempDir()).path)
        pkg_dir.create(self.__pkg_dir)
        write_file(self.__pkg_dir / 'output/output1', self.__OUTPUT1)
        write_file(self.__pkg_dir / 'source1', self.__SOURCE1)
        write_file(self.__pkg_dir / 'source2', self.__SOURCE2)

    def when_archived(self):
        self.__zipfile = self.useFixture(FileFixture(b'')).file
        os.remove(self.__zipfile)
        m.create(self.__zipfile, self.__pkg_dir)

    def then_archive_contains_files_from_package_directory(self):
        z = zipfile.ZipFile(self.__zipfile)
        self.assertTrue(pkg_zip.is_valid(z))

        self.assertEquals(self.__OUTPUT1, z.read('data/output1'))
        self.assertEquals(self.__SOURCE2, z.read('code/source2'))

        files = z.namelist()
        self.assertIn('meta/pkgmeta', files)
        self.assertIn('meta/checksums', files)
