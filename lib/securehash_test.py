import os
import tempfile

import fixtures
from testtools import TestCase

from . import securehash


class FileFixture(fixtures.Fixture):

    def __init__(self, content):
        self.content = content

    def setUp(self):
        super(FileFixture, self).setUp()
        fd, self.file = tempfile.mkstemp()
        os.write(fd, self.content)
        os.close(fd)
        self.addCleanup(os.remove, self.file)


class Test(TestCase):

    def test_file(self):
        self.given_a_file()
        self.when_file_is_hashed()
        self.then_result_is_an_ascii_string_of_more_than_32_chars()

    def test_bytes(self):
        self.given_some_bytes()
        self.when_bytes_are_hashed()
        self.then_result_is_an_ascii_string_of_more_than_32_chars()

    # implementation

    __file = None
    __hashresult = None
    __some_bytes = None

    def given_a_file(self):
        self.__file = (
            self.useFixture(FileFixture(b'with some content')).file
        )

    def given_some_bytes(self):
        self.__some_bytes = b'some bytes'

    def when_bytes_are_hashed(self):
        self.__hashresult = securehash.bytes(self.__some_bytes)

    def when_file_is_hashed(self):
        with open(self.__file, 'rb') as f:
            self.__hashresult = securehash.file(f)

    def then_result_is_an_ascii_string_of_more_than_32_chars(self):
        self.__hashresult.encode('ascii')
        self.assertIsInstance(self.__hashresult, str)
        self.assertGreater(len(self.__hashresult), 32)
