from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from bead.test import TestCase
from testtools.matchers import Contains

from . import test_fixtures as fixtures
from collections import namedtuple
from bead import spec as bead_spec
from bead.workspace import Workspace


class Test(TestCase, fixtures.RobotAndBeads):

    def test_invalid_workspace_causes_error(self, robot):
        self.assertRaises(SystemExit, robot.cli, 'save')
        self.assertThat(robot.stderr, Contains('ERROR'))

    def test_on_success_there_is_feedback(self, robot, repo):
        robot.cli('new', 'bead')
        robot.cd('bead')
        robot.cli('save')
        self.assertNotEquals(
            robot.stdout, '', 'Expected some feedback, but got none :(')


class Test_no_repo(TestCase):

    # fixtures
    def robot(self):
        return self.useFixture(fixtures.Robot())

    # tests
    def test_missing_repo_causes_error(self, robot):
        robot.cli('new', 'bead')
        self.assertRaises(SystemExit, robot.cli, 'save', 'bead')
        self.assertThat(robot.stderr, Contains('ERROR'))


Repo = namedtuple('Repo', 'name directory')


def bead_count(robot, repo, bead_uuid):
    with robot.environment as env:
        query = [(bead_spec.BEAD_UUID, bead_uuid)]
        return sum(1 for _ in env.get_repo(repo.name).find_beads(query))


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
        robot.cli('new', 'bead')
        self.assertRaises(SystemExit, robot.cli, 'save', 'bead')
        self.assertThat(robot.stderr, Contains('ERROR'))

    def test_save_stores_bead_in_specified_repo(self, robot, repo1, repo2):
        robot.cli('new', 'bead')
        robot.cli('save', repo1.name, '--workspace=bead')
        with robot.environment:
            bead_uuid = Workspace('bead').bead_uuid
        self.assertEquals(1, bead_count(robot, repo1, bead_uuid))
        self.assertEquals(0, bead_count(robot, repo2, bead_uuid))
        robot.cli('save', repo2.name, '-w', 'bead')
        self.assertEquals(1, bead_count(robot, repo1, bead_uuid))
        self.assertEquals(1, bead_count(robot, repo2, bead_uuid))

    def test_invalid_repo_specified(self, robot, repo1, repo2):
        robot.cli('new', 'bead')
        self.assertRaises(
            SystemExit,
            robot.cli, 'save', 'unknown-repo', '--workspace', 'bead')
        self.assertThat(robot.stderr, Contains('ERROR'))
