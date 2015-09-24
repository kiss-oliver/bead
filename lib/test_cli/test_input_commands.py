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

    def assert_mounted(self, robot, input_name, package_name):
        self.assertThat(
            robot.cwd / 'input' / input_name / 'README',
            FileContains(package_name))

    # tests

    def test_basic_usage(self, robot, pkg_with_history):
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
