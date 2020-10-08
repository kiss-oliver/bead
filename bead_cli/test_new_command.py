import os
from bead.test import TestCase

from .test_robot import Robot


class Test_basic_command_line(TestCase):

    # fixtures
    def robot(self):
        return self.useFixture(Robot())

    def cli(self, robot):
        return robot.cli

    def cwd(self, robot):
        return robot.cwd

    def test_new_fails_if_directory_exists(self, cli, cwd, robot):
        os.makedirs(cwd / 'workspace')
        self.assertRaises(SystemExit, cli, 'new workspace')
        assert 'ERROR' in robot.stderr
        assert 'workspace' not in robot.stdout
