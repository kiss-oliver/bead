from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from bead.test import TestCase
from testtools.matchers import FileContains, Not, Contains, FileExists

from .test_robot import Robot

from bead.tech.timestamp import timestamp
from bead.workspace import Workspace

import os


class Test_shared_repo(TestCase):

    # fixtures
    def repo(self):
        return self.new_temp_dir()

    def timestamp(self):
        return timestamp()

    def bead(self, timestamp):
        tmp = self.new_temp_dir()
        ws = Workspace(tmp / 'ws')
        ws.create('bead-uuid')
        bead_archive = tmp / 'bead.zip'
        ws.pack(bead_archive, timestamp)
        return bead_archive

    def alice(self, repo):
        robot = self.useFixture(Robot())
        robot.cli('repo', 'add', 'bobrepo', repo)
        return robot

    def bob(self, repo):
        robot = self.useFixture(Robot())
        robot.cli('repo', 'add', 'alicerepo', repo)
        return robot

    # tests
    def test_update(self, alice, bob, bead):
        bob.cli('new', 'bobbead')
        bob.cd('bobbead')
        bob.cli('input', 'add', 'alicebead1', bead)
        bob.cli('input', 'add', 'alicebead2', bead)

        alice.cli('develop', bead, 'alicebead')
        alice.cd('alicebead')
        alice.write_file('output/datafile', '''Alice's new data''')
        alice.cli('save')

        # update only one input
        bob.cli('input', 'update', 'alicebead1')

        self.assertThat(
            bob.cwd / 'input/alicebead1/datafile',
            FileContains('''Alice's new data'''))

        # second input directory not changed
        self.assertThat(
            bob.cwd / 'input/alicebead2/datafile',
            Not(FileExists()))

        # update all inputs
        bob.cli('input', 'update')

        self.assertThat(
            bob.cwd / 'input/alicebead2/datafile',
            FileContains('''Alice's new data'''))


class Test_repo_commands(TestCase):

    # fixtures
    def robot(self):
        return self.useFixture(Robot())

    def dir1(self, robot):
        os.makedirs(robot.cwd / 'dir1')
        return 'dir1'

    def dir2(self, robot):
        os.makedirs(robot.cwd / 'dir2')
        return 'dir2'

    # tests
    def test_list_when_there_are_no_repos(self, robot):
        robot.cli('repo', 'list')
        self.assertThat(
            robot.stdout, Contains('There are no defined repositories'))

    def test_add_non_existing_directory_fails(self, robot):
        robot.cli('repo', 'add', 'notadded', 'non-existing')
        self.assertThat(robot.stdout, Contains('ERROR'))
        self.assertThat(robot.stdout, Not(Contains('notadded')))

    def test_add_multiple(self, robot, dir1, dir2):
        robot.cli('repo', 'add', 'name1', 'dir1')
        robot.cli('repo', 'add', 'name2', 'dir2')
        self.assertThat(robot.stdout, Not(Contains('ERROR')))

        robot.cli('repo', 'list')
        self.assertThat(robot.stdout, Contains('name1'))
        self.assertThat(robot.stdout, Contains('name2'))
        self.assertThat(robot.stdout, Contains('dir1'))
        self.assertThat(robot.stdout, Contains('dir2'))

    def test_add_with_same_name_fails(self, robot, dir1, dir2):
        robot.cli('repo', 'add', 'name', 'dir1')
        self.assertThat(robot.stdout, Not(Contains('ERROR')))

        robot.cli('repo', 'add', 'name', 'dir2')
        self.assertThat(robot.stdout, Contains('ERROR'))

    def test_add_same_directory_twice_fails(self, robot, dir1):
        robot.cli('repo', 'add', 'name1', dir1)
        self.assertThat(robot.stdout, Not(Contains('ERROR')))

        robot.cli('repo', 'add', 'name2', dir1)
        self.assertThat(robot.stdout, Contains('ERROR'))

    def test_forget_repo(self, robot, dir1, dir2):
        robot.cli('repo', 'add', 'repo-to-delete', dir1)
        robot.cli('repo', 'add', 'another-repo', dir2)

        robot.cli('repo', 'forget', 'repo-to-delete')
        self.assertThat(robot.stdout, Contains('forgotten'))

        robot.cli('repo', 'list')
        self.assertThat(robot.stdout, Not(Contains('repo-to-delete')))
        self.assertThat(robot.stdout, Contains('another-repo'))

    def test_forget_nonexisting_repo(self, robot):
        robot.cli('repo', 'forget', 'non-existing')
        self.assertThat(robot.stdout, Contains('WARNING'))
