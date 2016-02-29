from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase
from testtools.matchers import Not, Contains

from . import fixtures


class Test_status(TestCase, fixtures.RobotAndPackages):

    # tests

    def test(self, robot, packages, pkg_with_inputs, pkg_a):
        robot.cli('develop', pkg_with_inputs)
        robot.cd(pkg_with_inputs)
        robot.cli('status')

        self.assertThat(robot.stdout, Contains(pkg_with_inputs))
        self.assertThat(robot.stdout, Contains(pkg_a))

        pkg_a = packages[pkg_a]
        pkg_with_inputs = packages[pkg_with_inputs]
        self.assertThat(robot.stdout, Not(Contains(pkg_with_inputs.uuid)))
        self.assertThat(robot.stdout, Not(Contains(pkg_a.uuid)))
        self.assertThat(robot.stdout, Contains(pkg_a.timestamp_str))
        self.assertThat(robot.stdout, Not(Contains(pkg_a.version)))

    def test_verbose(self, robot, packages, pkg_with_inputs, pkg_a):
        robot.cli('develop', pkg_with_inputs)
        robot.cd(pkg_with_inputs)
        robot.cli('status', '-v')

        self.assertThat(robot.stdout, Contains(pkg_with_inputs))
        self.assertThat(robot.stdout, Contains(pkg_a))

        pkg_a = packages[pkg_a]
        pkg_with_inputs = packages[pkg_with_inputs]
        self.assertThat(robot.stdout, Contains(pkg_with_inputs.uuid))
        self.assertThat(robot.stdout, Contains(pkg_a.uuid))
        self.assertThat(robot.stdout, Contains(pkg_a.timestamp_str))
        self.assertThat(robot.stdout, Contains(pkg_a.version))

    def test_inputs_not_in_known_repos(
            self, robot, packages, pkg_with_inputs, pkg_a):
        robot.cli('develop', pkg_with_inputs)
        robot.cd(pkg_with_inputs)

        robot.reset()
        robot.cli('status')

        self.assertThat(robot.stdout, Not(Contains(pkg_with_inputs)))
        self.assertThat(robot.stdout, Not(Contains(pkg_a)))

        pkg_a = packages[pkg_a]
        pkg_with_inputs = packages[pkg_with_inputs]
        self.assertThat(robot.stdout, Contains(pkg_with_inputs.uuid))
        self.assertThat(robot.stdout, Contains(pkg_a.uuid))
        self.assertThat(robot.stdout, Not(Contains(pkg_a.timestamp_str)))
        self.assertThat(robot.stdout, Contains(pkg_a.version))

    def test_verbose_inputs_not_in_known_repos(
            self, robot, packages, pkg_with_inputs, pkg_a):
        robot.cli('develop', pkg_with_inputs)
        robot.cd(pkg_with_inputs)
        robot.reset()
        robot.cli('status', '--verbose')

        self.assertThat(robot.stdout, Not(Contains(pkg_with_inputs)))
        self.assertThat(robot.stdout, Not(Contains(pkg_a)))

        pkg_a = packages[pkg_a]
        pkg_with_inputs = packages[pkg_with_inputs]
        self.assertThat(robot.stdout, Contains(pkg_with_inputs.uuid))
        self.assertThat(robot.stdout, Contains(pkg_a.uuid))
        self.assertThat(robot.stdout, Not(Contains(pkg_a.timestamp_str)))
        self.assertThat(robot.stdout, Contains(pkg_a.version))

    def test_invalid_workspace(self, robot):
        robot.cli('status')
        self.assertThat(robot.stderr, Contains('WARNING'))
