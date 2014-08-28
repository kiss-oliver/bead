from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase
from . import workspace as m

import zipfile

from ..path import write_file, ensure_directory
from .archive import Archive


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


class Test_pack(TestCase):

    def test_creates_valid_archive(self):
        self.given_a_package_directory()
        self.when_archived()
        self.then_archive_is_valid_package()

    def test_archives_all_content(self):
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
        m.Workspace(self.__pkg_dir).create()
        write_file(self.__pkg_dir / 'output/output1', self.__OUTPUT1)
        write_file(self.__pkg_dir / 'source1', self.__SOURCE1)
        ensure_directory(self.__pkg_dir / 'subdir')
        write_file(self.__pkg_dir / 'subdir/source2', self.__SOURCE2)

    def when_archived(self):
        self.__zipfile = m.Workspace(self.__pkg_dir).pack()

    def then_archive_contains_files_from_package_directory(self):
        z = zipfile.ZipFile(self.__zipfile)

        self.assertEquals(self.__OUTPUT1, z.read('data/output1'))
        self.assertEquals(self.__SOURCE1, z.read('code/source1'))
        self.assertEquals(self.__SOURCE2, z.read('code/subdir/source2'))

        files = z.namelist()
        self.assertIn('meta/pkgmeta', files)
        self.assertIn('meta/checksums', files)

    def then_archive_is_valid_package(self):
        with Archive(self.__zipfile) as pkg:
            self.assertTrue(pkg.is_valid)
