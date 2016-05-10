from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from bead.test import TestCase
from testtools.matchers import Contains

from . import fixtures


class Test_nuke(TestCase, fixtures.RobotAndBeads):

    # tests

    def test_with_default_workspace(self, robot, bead_with_inputs):
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)
        robot.cli('nuke')

        self.assertThat(robot.stdout, Contains(bead_with_inputs))

    def test_with_explicit_workspace(self, robot, bead_with_inputs):
        robot.cli('develop', bead_with_inputs)
        robot.cli('nuke', bead_with_inputs)

        self.assertThat(robot.stdout, Contains(bead_with_inputs))

    def test_invalid_workspace(self, robot):
        self.assertRaises(SystemExit, robot.cli, 'nuke')
        self.assertThat(robot.stderr, Contains('ERROR'))
