from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase
from testtools.matchers import FileContains, Not, Contains

import os
from ..pkg.workspace import Workspace
from . import fixtures


class Test_input_commands(TestCase, fixtures.RobotAndPackages):

    def assert_loaded(self, robot, input_name, package_name):
        self.assertThat(
            robot.cwd / 'input' / input_name / 'README',
            FileContains(package_name))

    # tests

    def test_basic_usage(self, robot, pkg_with_history):
        # nextpkg with input1 as datapkg1
        robot.cli('new', 'nextpkg')
        robot.cd('nextpkg')
        robot.cli('input', 'add', 'input1', 'pkg_with_history@' + fixtures.TS1)
        robot.cli('save')
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

    def test_update_unloaded_input_with_explicit_package(
            self, robot, pkg_with_inputs, pkg_a, pkg_b):
        robot.cli('develop', pkg_with_inputs)
        robot.cd(pkg_with_inputs)

        assert not Workspace(robot.cwd).is_loaded('input_b')

        robot.cli('input', 'update', 'input_b', pkg_a)
        self.assert_loaded(robot, 'input_b', pkg_a)

        robot.cli('status')
        self.assertThat(robot.stdout, Not(Contains(pkg_b)))

    def test_load_on_workspace_without_input_gives_feedback(
            self, robot, pkg_a):
        robot.cli('develop', pkg_a)
        robot.cd(pkg_a)
        robot.cli('input', 'load')

        self.assertThat(robot.stderr, Contains('WARNING'))
        self.assertThat(robot.stderr, Contains('No inputs defined to load.'))

    def test_load_with_missing_package_gives_warning(
            self, robot, pkg_with_inputs, pkg_a):
        robot.cli('develop', pkg_with_inputs)
        robot.cd(pkg_with_inputs)
        robot.reset()
        robot.cli('input', 'load')
        self.assertThat(robot.stderr, Contains('WARNING'))
        self.assertThat(robot.stderr, Contains('input_a'))
        self.assertThat(robot.stderr, Contains('input_b'))

    def test_load_only_one_input(
            self, robot, pkg_with_inputs, pkg_a):
        robot.cli('develop', pkg_with_inputs)
        robot.cd(pkg_with_inputs)
        robot.cli('input', 'load', 'input_a')
        self.assert_loaded(robot, 'input_a', pkg_a)
        with robot.environment:
            self.assertFalse(Workspace('.').is_loaded('input_b'))

    def test_partially_deleted_repo(self, robot, pkg_with_inputs):
        deleted_repo = self.new_temp_dir()
        robot.cli('repo', 'add', 'missing', deleted_repo)
        os.rmdir(deleted_repo)
        robot.cli('develop', pkg_with_inputs)
        robot.cd(pkg_with_inputs)
        robot.cli('input', 'load')

    def test_add_with_unrecognized_package_name_exits_with_error(
            self, robot, pkg_a):
        robot.cli('develop', pkg_a)
        robot.cd(pkg_a)
        try:
            robot.cli('input', 'add', 'x', 'non-existing-package')
            self.fail('Expected an error exit!')
        except SystemExit:
            self.assertThat(robot.stderr, Contains('ERROR'))
            self.assertThat(robot.stderr, Contains('non-existing-package'))

    def test_add_with_hacked_package_is_refused(
            self, robot, hacked_pkg, pkg_a):
        robot.cli('develop', pkg_a)
        robot.cd(pkg_a)
        robot.cli('input', 'add', 'hack', hacked_pkg)
        self.assertFalse(Workspace(robot.cwd).has_input('hack'))
        self.assertThat(robot.stderr, Contains('WARNING'))

    def test_update_with_hacked_package_is_refused(
            self, robot, hacked_pkg, pkg_a):
        robot.cli('develop', pkg_a)
        robot.cd(pkg_a)
        robot.cli('input', 'add', 'intelligence', pkg_a)
        robot.cli('input', 'update', 'intelligence', hacked_pkg)
        self.assertThat(
            robot.cwd / 'input/intelligence/README',
            FileContains(pkg_a))
        self.assertThat(robot.stderr, Contains('WARNING'))
