from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from bead.test import TestCase
from testtools.content import text_content

from .robot import Robot


class Test_basic_command_line(TestCase):

    # fixtures
    def robot(self):
        return self.useFixture(Robot())

    def cli(self, robot):
        return robot.cli

    def cd(self, robot):
        return robot.cd

    def ls(self, robot):
        return robot.ls

    def repo_dir(self):
        return self.new_temp_dir()

    # tests
    def test(self, robot, cli, cd, ls, repo_dir):
        self.addDetail('home', text_content(robot.home))

        cli('new', 'something')
        self.assertIn('something', robot.stdout)

        cd('something')
        cli('status')
        self.assertNotIn('Inputs', robot.stdout)

        cli('repo', 'add', 'default', repo_dir)
        cli('save')

        cd('..')
        cli('develop', 'something', 'something-develop')
        self.assertIn(robot.cwd / 'something-develop', ls())

        cd('something-develop')
        cli('input', 'add', 'older-self', 'something')
        cli('status')
        self.assertIn('Inputs', robot.stdout)
        self.assertIn('older-self', robot.stdout)

        cli('nuke', robot.cwd.parent / 'something')
        cli('nuke')

        cd('..')
        self.assertEqual([], ls(robot.home))
