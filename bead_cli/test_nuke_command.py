from bead.test import TestCase

from . import test_fixtures as fixtures


class Test_nuke(TestCase, fixtures.RobotAndBeads):

    # tests

    def test_with_default_workspace(self, robot, bead_with_inputs):
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)
        robot.cli('nuke')

        assert bead_with_inputs in robot.stdout

    def test_with_explicit_workspace(self, robot, bead_with_inputs):
        robot.cli('develop', bead_with_inputs)
        robot.cli('nuke', bead_with_inputs)

        assert bead_with_inputs in robot.stdout

    def test_invalid_workspace(self, robot):
        self.assertRaises(SystemExit, robot.cli, 'nuke')
        assert 'ERROR' in robot.stderr
