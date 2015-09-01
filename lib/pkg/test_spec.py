from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from . import spec as m
import unittest


class Test_parse(unittest.TestCase):

    def assert_parsed(self, spec, peer, name, version, offset):
        parsed = m.parse(spec)
        self.assertEqual(
            (peer, name, version, offset),
            (parsed.peer, parsed.name, parsed.version, parsed.offset))

    def test_all_parts(self):
        self.assert_parsed(
            'peer:package-name@version-1',
            'peer', 'package-name', 'version', 1)

    def test_peer_is_optional(self):
        self.assert_parsed(
            'package-name@version',
            '', 'package-name', 'version', 0)

    def test_empty_peer_is_ok(self):
        self.assert_parsed(
            ':package-name@version',
            '', 'package-name', 'version', 0)

    def test_version_is_optional(self):
        self.assert_parsed(
            'peer:package-name',
            'peer', 'package-name', None, 0)

    def test_empty_string_is_parsed_as_version(self):
        self.assert_parsed(
            'peer:package-name@',
            'peer', 'package-name', None, 0)

    def test_empty_string_with_offset_is_parsed_as_version_with_offset(self):
        self.assert_parsed(
            'peer:package-name@-1',
            'peer', 'package-name', None, 1)

    def test_empty_string_is_not_parsed_as_package_name(self):
        self.assertRaises(ValueError, m.parse, 'peer:@version1')

if __name__ == '__main__':
    unittest.main()
