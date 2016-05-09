from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase, skip
from testtools.matchers import FileContains, Contains, FileExists

from ..pkg.workspace import Workspace
from ..pkg import layouts
from . import fixtures


class Test_develop(TestCase, fixtures.RobotAndBeads):

    # tests
    def test_by_name(self, robot, bead_a):
        robot.cli('develop', bead_a)

        self.assertTrue(Workspace(robot.cwd / bead_a).is_valid)
        self.assertThat(robot.cwd / bead_a / 'README', FileContains(bead_a))

    def test_missing_bead(self, robot, bead_a):
        robot.cli('repo', 'forget', 'repo')
        try:
            robot.cli('develop', bead_a)
        except SystemExit:
            self.assertThat(robot.stderr, Contains('Bead'))
            self.assertThat(robot.stderr, Contains('not found'))
        else:
            self.fail('develop should have exited on missing bead')

    def assert_develop_version(self, robot, bead_spec, timestamp):
        assert bead_spec.startswith('bead_with_history')
        robot.cli('develop', bead_spec)
        self.assertThat(
            robot.cwd / 'bead_with_history' / 'sentinel-' + timestamp,
            FileExists())

    def test_without_version(self, robot, bead_with_history):
        self.assert_develop_version(robot, 'bead_with_history', fixtures.TS2)

    @skip('bead version')
    def test_without_offset(self, robot, bead_with_history):
        self.assert_develop_version(robot, 'bead_with_history@', fixtures.TS2)

    @skip('bead version')
    def test_with_offset(self, robot, bead_with_history):
        self.assert_develop_version(robot, 'bead_with_history@-1', fixtures.TS1)

    @skip('bead version')
    def test_with_version_without_offset(self, robot, bead_with_history):
        self.assert_develop_version(
            robot, 'bead_with_history@' + fixtures.TS1,
            fixtures.TS1)

    @skip('bead version')
    def test_available_matches_to_version_are_less_than_offset(
            self, robot, bead_with_history):
        self.assert_develop_version(
            robot, 'bead_with_history@{}-1'.format(fixtures.TS2), fixtures.TS2)

    def test_hacked_bead_is_detected(self, robot, hacked_bead):
        self.assertRaises(SystemExit, robot.cli, 'develop', hacked_bead)
        self.assertThat(robot.stderr, Contains('ERROR'))

    def test_extract_output(self, robot, bead_a):
        robot.cli('develop', '-x', bead_a)
        ws = robot.cwd / bead_a

        self.assertTrue(Workspace(ws).is_valid)

        # output must be unpacked as well!
        self.assertThat(
            ws / layouts.Workspace.OUTPUT / 'README',
            FileContains(bead_a))
