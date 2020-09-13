from .test import TestCase
from . import archive as m

import os
import zipfile

from . import layouts


class Test_Archive(TestCase):

    def test_extract_file(self):
        self.given_a_bead()
        self.when_file1_is_extracted()
        self.then_file1_has_the_expected_content()

    def test_extract_dir(self):
        self.given_a_bead()
        self.when_a_directory_is_extracted()
        self.then_directory_has_the_expected_files()
        self.then_file1_has_the_expected_content()

    def test_extract_nonexistant_dir(self):
        self.given_a_bead()
        self.when_a_nonexistent_directory_is_extracted()
        self.then_an_empty_directory_is_created()

    def test_content_id(self):
        self.given_a_bead()
        self.when_content_id_is_checked()
        self.then_content_id_is_a_string()

    # implementation

    __bead = None
    __extractedfile = None
    __extracteddir = None
    __content_id = None

    def given_a_bead(self):
        # yields an invalid BEAD (meta is simplified), sufficient for unit testing
        self.__bead = self.new_temp_dir() / 'bead.zip'
        with zipfile.ZipFile(self.__bead, 'w') as z:
            z.writestr(
                layouts.Archive.BEAD_META,
                b'''
                    {
                        "meta_version": "aaa947a6-1f7a-11e6-ba3a-0021cc73492e",
                        "kind": "TEST-FAKE",
                        "freeze_time": "20200913T173910000000+0000"
                    }
                ''')
            z.writestr('somefile1', b'''somefile1's known content''')
            z.writestr('path/file1', b'''?? file1's known content''')
            z.writestr('path/to/file1', b'''file1's known content''')
            z.writestr('path/to/file2', b'''file2's known content''')
            z.writestr(layouts.Archive.MANIFEST, b'some manifest')

    def when_file1_is_extracted(self):
        self.__extractedfile = self.new_temp_dir() / 'extracted_file'
        bead = m.Archive(self.__bead)
        bead.extract_file('path/to/file1', self.__extractedfile)

    def then_file1_has_the_expected_content(self):
        with open(self.__extractedfile, 'rb') as f:
            assert b'''file1's known content''' == f.read()

    def when_a_directory_is_extracted(self):
        self.__extracteddir = self.new_temp_dir() / 'destination dir'
        bead = m.Archive(self.__bead)
        bead.extract_dir('path/to', self.__extracteddir)
        self.__extractedfile = os.path.join(self.__extracteddir, 'file1')

    def then_directory_has_the_expected_files(self):
        assert {'file1', 'file2'} == set(os.listdir(self.__extracteddir))

    def when_content_id_is_checked(self):
        bead = m.Archive(self.__bead)
        self.__content_id = bead.content_id

    def then_content_id_is_a_string(self):
        assert isinstance(self.__content_id, str)

    def when_a_nonexistent_directory_is_extracted(self):
        self.__extracteddir = self.new_temp_dir() / 'destination dir'
        bead = m.Archive(self.__bead)
        bead.extract_dir('path/to/nonexistent', self.__extracteddir)

    def then_an_empty_directory_is_created(self):
        assert os.path.isdir(self.__extracteddir)
        assert [] == os.listdir(self.__extracteddir)
