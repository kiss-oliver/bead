from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import unittest
from ..test import TestCase
from .robot import Robot

import os

from ..translations import Peer


class Test(TestCase):

    # fixtures

    def package_uuid(self):
        return 'TEST package_uuid'

    def name(self):
        return 'TEST package name'

    def robot(self, name, package_uuid):
        '''
            robot with a knowledge about package :name
        '''
        robot = self.useFixture(Robot())
        robot.cli('dict', 'add', name, package_uuid)
        return robot

    # checks

    def assert_translation(self, robot, peer, name, package_uuid):
        with robot.environment:
            self.assertEqual(
                Peer.by_name(peer).get_translation(name).package_uuid,
                package_uuid)

    def assert_unknown(self, robot, name):
        with robot.environment:
            self.assertFalse(Peer.self().knows_about(name))

    # tests

    def test_add(self, robot, name, package_uuid):
        robot.cli('dict', 'add', 'another-name', package_uuid)
        self.assert_translation(robot, Peer.SELF, name, package_uuid)
        self.assert_translation(robot, Peer.SELF, 'another-name', package_uuid)

    def test_export_import(self, robot, name, package_uuid):
        robot.cli('dict', 'export', 'exported_names')
        robot.reset()
        #
        self.assertTrue(os.path.isfile(robot.cwd / 'exported_names'))
        robot.cli('dict', 'import', 'old-self', 'exported_names')
        #
        self.assert_translation(robot, 'old-self', name, package_uuid)

    def test_rename(self, robot, name, package_uuid):
        robot.cli('dict', 'rename', name, 'new-name')
        self.assert_translation(robot, Peer.SELF, 'new-name', package_uuid)
        self.assert_unknown(robot, name)

    def test_forget(self, robot, name):
        robot.cli('dict', 'forget', name)
        self.assert_unknown(robot, name)

    def test_merge(self, robot, name, package_uuid):
        robot.cli('dict', 'add', 'conflicting-name', 'should not be imported')
        robot.cli('dict', 'export', 'export-file')
        robot.reset()
        #
        robot.cli('dict', 'add', 'conflicting-name', package_uuid)
        robot.cli('dict', 'import', 'old-self', 'export-file')
        robot.cli('dict', 'merge', 'old-self')
        #
        self.assert_translation(
            robot, Peer.SELF, name, package_uuid)
        self.assert_translation(
            robot, Peer.SELF, 'conflicting-name', package_uuid)

    @unittest.skip('unimplemented')
    def test_copy(self):
        assert False, 'unimplemented'


'''
dict

    export
        -p peer
        -o filename

    import
        peer
        filename

    add
        name
        package_uuid

    merge
        peer

    copy
        [peer:]name
        new-name

    rename
        old-name
        new-name

    forget
        -p peer|-n name

    list
        [re-filter]
'''
