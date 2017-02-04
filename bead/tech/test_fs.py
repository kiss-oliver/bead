# coding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase
from . import fs as m

import os


class TestPath(TestCase):

    def test_div(self):
        result = m.Path('a') / 'b' / '..' / 'b'
        self.assertEquals(('a', '/', 'b'), result.partition('/'))


class Test_make_readonly(TestCase):

    def test_file(self):
        self.given_a_file()
        self.when_made_readonly()
        self.then_file_can_not_be_written()

    def test_directory(self):
        self.given_a_directory()
        self.when_made_readonly()
        self.then_can_not_creat_file_under_directory()

    # implementation

    __path = None

    def given_a_file(self):
        self.__path = self.new_temp_dir() / 'file'
        with open(self.__path, 'wb'):
            pass

    def given_a_directory(self):
        self.__path = self.new_temp_dir()

    def when_made_readonly(self):
        m.make_readonly(self.__path)

    def then_file_can_not_be_written(self):
        self.assertRaises(IOError, open, self.__path, 'wb')

    def then_can_not_creat_file_under_directory(self):
        self.assertRaises(IOError, open, self.__path / 'file', 'wb')


class Test_make_writable(TestCase):

    def test_file(self):
        self.given_a_read_only_file()
        self.when_made_writable()
        self.then_file_can_be_written()

    def test_directory(self):
        self.given_a_read_only_directory()
        self.when_made_writable()
        self.then_file_can_be_created_under_directory()

    # implementation

    __path = None

    def given_a_read_only_file(self):
        self.__path = self.new_temp_dir() / 'file'
        with open(self.__path, 'wb'):
            pass
        m.make_readonly(self.__path)

    def given_a_read_only_directory(self):
        self.__path = self.new_temp_dir()
        m.make_readonly(self.__path)

    def when_made_writable(self):
        m.make_writable(self.__path)

    def then_file_can_be_written(self):
        with open(self.__path, 'ab') as f:
            f.write(b'little something')

    def then_file_can_be_created_under_directory(self):
        with open(self.__path / 'file', 'wb') as f:
            f.write(b'little something')


class Test_all_subpaths(TestCase):

    def test(self):
        self.given_some_directory_structure_with_files()
        self.when_all_paths_are_collected()
        self.then_all_paths_are_found()

    # implementation

    __root = None
    DIRS = ('a', 'b', 'c', 'c/d')
    FILES = ('a/f', 'c/d/f1', 'c/d/f2')

    def given_some_directory_structure_with_files(self):
        self.__root = root = self.new_temp_dir()
        for dir in self.DIRS:
            os.makedirs(root / dir)
        for f in self.FILES:
            m.write_file(root / f, '')

    def when_all_paths_are_collected(self):
        self.__paths = set(m.all_subpaths(self.__root))

    def then_all_paths_are_found(self):
        root = self.__root
        self.assertEquals(
            {root}
            | set(root / d for d in self.DIRS)
            | set(root / f for f in self.FILES),
            self.__paths
        )


class Test_read_write_file(TestCase):

    def test(self):
        root = self.new_temp_dir()
        testfile = root / 'testfile'
        content = u'Test_read_write_file testfile content / áíőóüú@!#@!#$$@'
        m.write_file(testfile, content)
        self.assertEquals(content, m.read_file(testfile))
