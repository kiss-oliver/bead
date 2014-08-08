from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase
from . import pkg_zip as m

import os
import zipfile


class Test_Package_extractions(TestCase):

    def test_extract_file(self):
        self.given_a_package()
        self.when_file1_is_extracted()
        self.then_file1_has_the_expected_content()

    def test_extract_dir(self):
        self.given_a_package()
        self.when_a_directory_is_extracted()
        self.then_directory_has_the_expected_files()
        self.then_file1_has_the_expected_content()

    # implementation

    __package = None
    __extractedfile = None
    __extracteddir = None

    def given_a_package(self):
        self.__package = self.new_temp_dir() / 'package.zip'
        z = zipfile.ZipFile(self.__package, 'w')
        z.writestr('somefile1', b'''somefile1's known content''')
        z.writestr('path/file1', b'''?? file1's known content''')
        z.writestr('path/to/file1', b'''file1's known content''')
        z.writestr('path/to/file2', b'''file2's known content''')
        z.close()

    def when_file1_is_extracted(self):
        self.__extractedfile = self.new_temp_dir() / 'extracted_file'
        with m.Package(self.__package) as pkg:
            pkg.extract_file('path/to/file1', self.__extractedfile)

    def then_file1_has_the_expected_content(self):
        with open(self.__extractedfile, 'rb') as f:
            self.assertEquals(b'''file1's known content''', f.read())

    def when_a_directory_is_extracted(self):
        self.__extracteddir = self.new_temp_dir() / 'destination dir'
        with m.Package(self.__package) as pkg:
            pkg.extract_dir('path/to', self.__extracteddir)
        self.__extractedfile = os.path.join(self.__extracteddir, 'file1')

    def then_directory_has_the_expected_files(self):
        self.assertEquals(
            {'file1', 'file2'},
            set(os.listdir(self.__extracteddir))
        )
