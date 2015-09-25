from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase
from testtools.matchers import Contains

from . import fixtures


class Test(TestCase, fixtures.RobotAndPackages):

    def test_invalid_workspace_causes_error(self, robot):
        self.assertRaises(SystemExit, robot.cli, 'pack')
        self.assertThat(robot.stderr, Contains('ERROR'))

    def test_on_success_there_is_feedback(self, robot, repo):
        robot.cli('new', 'pkg')
        robot.cli('pack', 'pkg')
        self.assertNotEquals(
            robot.stdout, '', 'Expected some feedback, but got none :(')


class Test_no_repo(TestCase):

    # fixtures
    def robot(self):
        return self.useFixture(fixtures.Robot())

    # tests
    def test_missing_repo_causes_error(self, robot):
        robot.cli('new', 'pkg')
        self.assertRaises(SystemExit, robot.cli, 'pack', 'pkg')
        self.assertThat(robot.stderr, Contains('ERROR'))
