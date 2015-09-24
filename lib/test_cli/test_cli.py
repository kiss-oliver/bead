from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase
from testtools.matchers import FileContains, Not, Contains, FileExists

import os
from ..pkg.workspace import Workspace
from . import fixtures


class Test_package_with_history(TestCase, fixtures.RobotAndPackages):

    # tests
    def test_develop_by_name(self, robot, pkg_a):
        robot.cli('develop', pkg_a)

        self.assertTrue(Workspace(robot.cwd / pkg_a).is_valid)
        self.assertThat(robot.cwd / pkg_a / 'README', FileContains(pkg_a))

    def test_develop_missing_package(self, robot, pkg_a):
        robot.cli('repo', 'forget', 'repo')
        try:
            robot.cli('develop', pkg_a)
        except SystemExit:
            self.assertThat(robot.stderr, Contains('Package'))
            self.assertThat(robot.stderr, Contains('not found'))
        else:
            self.fail('develop should have exited on missing package')

    def assert_develop_version(self, robot, pkg_spec, timestamp):
        assert pkg_spec.startswith('pkg_with_history')
        robot.cli('develop', pkg_spec)
        self.assertThat(
            robot.cwd / 'pkg_with_history' / 'sentinel-' + timestamp,
            FileExists())

    def test_develop_without_version(self, robot, pkg_with_history):
        self.assert_develop_version(robot, 'pkg_with_history', fixtures.TS2)

    def test_develop_without_offset(self, robot, pkg_with_history):
        self.assert_develop_version(robot, 'pkg_with_history@', fixtures.TS2)

    def test_develop_with_offset(self, robot, pkg_with_history):
        self.assert_develop_version(robot, 'pkg_with_history@-1', fixtures.TS1)

    def test_develop_w_version_wo_offset(self, robot, pkg_with_history):
        self.assert_develop_version(
            robot, 'pkg_with_history@' + fixtures.TS1,
            fixtures.TS1)

    def test_develop_available_matches_to_version_are_less_than_offset(
            self, robot, pkg_with_history):
        self.assert_develop_version(
            robot, 'pkg_with_history@{}-1'.format(fixtures.TS2), fixtures.TS2)


class Test_input_commands(TestCase, fixtures.RobotAndPackages):

    def assert_mounted(self, robot, input_name, package_name):
        self.assertThat(
            robot.cwd / 'input' / input_name / 'README',
            FileContains(package_name))

    # tests

    def test_input_commands(self, robot, pkg_with_history):
        # nextpkg with input1 as datapkg1
        robot.cli('new', 'nextpkg')
        robot.cd('nextpkg')
        robot.cli('input', 'add', 'input1', 'pkg_with_history@' + fixtures.TS1)
        robot.cli('pack')
        robot.cd('..')
        robot.cli('nuke', 'nextpkg')

        robot.cli('develop', 'nextpkg')
        robot.cd('nextpkg')
        assert not os.path.exists(robot.cwd / 'input/input1')

        robot.cli('input', 'load')
        assert os.path.exists(robot.cwd / 'input/input1')

        robot.cli('input', 'add', 'input2', 'pkg_with_history')
        assert os.path.exists(robot.cwd / 'input/input2')

        robot.cli('input', 'delete', 'input1')
        assert not os.path.exists(robot.cwd / 'input/input1')

        # no-op load do not crash
        robot.cli('input', 'load')

        robot.cli('status')

    def test_update_unmounted_input_with_explicit_package(
            self, robot, pkg_with_inputs, pkg_a, pkg_b):
        robot.cli('develop', pkg_with_inputs)
        robot.cd(pkg_with_inputs)

        assert not Workspace(robot.cwd).is_mounted('input_b')

        robot.cli('input', 'update', 'input_b', pkg_a)
        self.assert_mounted(robot, 'input_b', pkg_a)

        robot.cli('status')
        self.assertThat(robot.stdout, Not(Contains(pkg_b)))
