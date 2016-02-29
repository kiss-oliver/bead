from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from . import spec as m
import unittest


class Test_parse(unittest.TestCase):

    def assert_parsed(self, spec, repo, name, version, offset):
        parsed = m.parse(spec)
        self.assertEqual(
            (repo, name, version, offset),
            (parsed.repo, parsed.name, parsed.version, parsed.offset))

    def test_all_parts(self):
        self.assert_parsed(
            'repo:package-name@version-1',
            'repo', 'package-name', 'version', 1)

    def test_repo_is_optional(self):
        self.assert_parsed(
            'package-name@version',
            m.ALL_REPOSITORIES, 'package-name', 'version', 0)

    def test_empty_repo_is_ok(self):
        self.assert_parsed(
            ':package-name@version',
            m.ALL_REPOSITORIES, 'package-name', 'version', 0)

    def test_version_is_optional(self):
        self.assert_parsed(
            'repo:package-name',
            'repo', 'package-name', None, 0)

    def test_empty_string_is_parsed_as_version(self):
        self.assert_parsed(
            'repo:package-name@',
            'repo', 'package-name', None, 0)

    def test_empty_string_with_offset_is_parsed_as_version_with_offset(self):
        self.assert_parsed(
            'repo:package-name@-1',
            'repo', 'package-name', None, 1)

    def test_empty_string_is_not_parsed_as_package_name(self):
        self.assertRaises(ValueError, m.parse, 'repo:@version1')

if __name__ == '__main__':
    unittest.main()
