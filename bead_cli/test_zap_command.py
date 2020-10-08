from bead.test import TestCase

from . import test_fixtures as fixtures


class Test_zap(TestCase, fixtures.RobotAndBeads):

    # tests

    def test_with_default_workspace(self, robot, bead_with_inputs):
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)
        robot.cli('zap')

        assert bead_with_inputs in robot.stdout

    def test_with_explicit_workspace(self, robot, bead_with_inputs):
        robot.cli('develop', bead_with_inputs)
        robot.cli('zap', bead_with_inputs)

        assert bead_with_inputs in robot.stdout

    def test_invalid_workspace(self, robot):
        self.assertRaises(SystemExit, robot.cli, 'zap')
        assert 'ERROR' in robot.stderr
