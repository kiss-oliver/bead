import os
from bead.test import TestCase

from .test_robot import Robot


class Test_basic_command_line(TestCase):

    # fixtures
    def robot(self):
        return self.useFixture(Robot())

    def cli(self, robot):
        return robot.cli

    def cd(self, robot):
        return robot.cd

    def ls(self, robot):
        return robot.ls

    def box_dir(self):
        return self.new_temp_dir()

    # tests
    def test(self, robot, cli, cd, ls, box_dir):
        print(f'home: {robot.home}')

        cli('new', 'something')
        assert 'something' in robot.stdout

        cd('something')
        cli('status')
        assert 'Inputs' not in robot.stdout

        cli('box', 'add', 'default', box_dir)
        cli('save')

        cd('..')
        cli('develop', 'something', 'something-develop')
        assert robot.cwd / 'something-develop' in ls()

        cd('something-develop')
        cli('input', 'add', 'older-self', 'something')
        cli('status')
        assert 'Inputs' in robot.stdout
        assert 'older-self' in robot.stdout

        cli('web')

        # this might leave behind the empty directory on windows
        cli('zap')
        cd('..')
        cli('zap', 'something')

        something_develop_dir = robot.home / 'something-develop'
        if os.path.exists(something_develop_dir):
            # on windows it is not possible to remove
            # the current working directory (zap does this)
            assert os.name != 'posix', 'Must be removed on posix'
            assert [] == ls(something_develop_dir)
            os.rmdir(something_develop_dir)
        assert [] == ls(robot.home)
