from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from .test import TestCase
from . import securehash

from .path import write_file


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
        self.__file = self.new_temp_dir() / 'file'
        write_file(self.__file, b'with some content')

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
