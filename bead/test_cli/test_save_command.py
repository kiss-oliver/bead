from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase
from testtools.matchers import Contains

from . import fixtures
from collections import namedtuple
from .. import repos
from ..pkg import spec as pkg_spec
from ..pkg.workspace import Workspace


class Test(TestCase, fixtures.RobotAndPackages):

    def test_invalid_workspace_causes_error(self, robot):
        self.assertRaises(SystemExit, robot.cli, 'save')
        self.assertThat(robot.stderr, Contains('ERROR'))

    def test_on_success_there_is_feedback(self, robot, repo):
        robot.cli('new', 'pkg')
        robot.cd('pkg')
        robot.cli('save')
        self.assertNotEquals(
            robot.stdout, '', 'Expected some feedback, but got none :(')


class Test_no_repo(TestCase):

    # fixtures
    def robot(self):
        return self.useFixture(fixtures.Robot())

    # tests
    def test_missing_repo_causes_error(self, robot):
        robot.cli('new', 'pkg')
        self.assertRaises(SystemExit, robot.cli, 'save', 'pkg')
        self.assertThat(robot.stderr, Contains('ERROR'))


Repo = namedtuple('Repo', 'name directory')


def package_count(robot, repo, pkg_uuid):
    with robot.environment:
        query = [(pkg_spec.BEAD_UUID, pkg_uuid)]
        return sum(1 for _ in repos.get(repo.name).find_packages(query))


class Test_more_than_one_repos(TestCase):
    # fixtures
    def robot(self):
        return self.useFixture(fixtures.Robot())

    def make_repo(self, robot, name):
        directory = self.new_temp_dir()
        robot.cli('repo', 'add', name, directory)
        return Repo(name, directory)

    def repo1(self, robot):
        return self.make_repo(robot, 'repo1')

    def repo2(self, robot):
        return self.make_repo(robot, 'repo2')

    # tests
    def test_save_dies_without_explicit_repo(self, robot, repo1, repo2):
        robot.cli('new', 'pkg')
        self.assertRaises(SystemExit, robot.cli, 'save', 'pkg')
        self.assertThat(robot.stderr, Contains('ERROR'))

    def test_save_stores_package_in_specified_repo(self, robot, repo1, repo2):
        robot.cli('new', 'pkg')
        robot.cli('save', repo1.name, '--workspace=pkg')
        with robot.environment:
            pkg_uuid = Workspace('pkg').uuid
        self.assertEquals(1, package_count(robot, repo1, pkg_uuid))
        self.assertEquals(0, package_count(robot, repo2, pkg_uuid))
        robot.cli('save', repo2.name, '-w', 'pkg')
        self.assertEquals(1, package_count(robot, repo1, pkg_uuid))
        self.assertEquals(1, package_count(robot, repo2, pkg_uuid))

    def test_invalid_repo_specified(self, robot, repo1, repo2):
        robot.cli('new', 'pkg')
        self.assertRaises(
            SystemExit,
            robot.cli, 'save', 'unknown-repo', '--workspace', 'pkg')
        self.assertThat(robot.stderr, Contains('ERROR'))
