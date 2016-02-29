from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TempDir

import os
import warnings
import zipfile

from ..pkg.workspace import Workspace
from ..pkg import layouts
from .. import tech
from .robot import Robot
from .. import repos


# timestamps
TS1 = '20150901_151015_1'
TS2 = '20150901_151016_2'


class RobotAndPackages(object):

    # fixtures
    def robot(self):
        '''
        I am a robot user with a repo
        '''
        robot = self.useFixture(Robot())
        repo_dir = robot.cwd / 'repo'
        os.makedirs(repo_dir)
        robot.cli('repo', 'add', 'repo', repo_dir)
        return robot

    def repo(self, robot):
        with robot.environment:
            return repos.get('repo')

    def packages(self):
        return {}

    def _new_package(self, robot, packages, package_name, inputs=None):
        robot.cli('new', package_name)
        robot.cd(package_name)
        robot.write_file('README', package_name)
        robot.write_file('output/README', package_name)
        self._add_inputs(robot, inputs)
        repo = self.repo(robot)
        with robot.environment:
            packages[package_name] = repo.store(Workspace('.'), TS1)
        robot.cd('..')
        robot.cli('nuke', package_name)
        return package_name

    def _add_inputs(self, robot, inputs):
        inputs = inputs or {}
        for name in inputs:
            robot.cli('input', 'add', name, inputs[name])

    def pkg_a(self, robot, packages):
        return self._new_package(robot, packages, 'pkg_a')

    def pkg_b(self, robot, packages):
        return self._new_package(robot, packages, 'pkg_b')

    def hacked_pkg(self, robot, packages):
        hacked_pkg_path = self.new_temp_dir() / 'hacked_pkg.zip'
        workspace_dir = self.new_temp_dir() / 'hacked_pkg'
        ws = Workspace(workspace_dir)
        ws.create('hacked-uuid')
        tech.fs.write_file(ws.directory / 'code', 'code')
        tech.fs.write_file(ws.directory / 'output/README', 'README')
        ws.pack(hacked_pkg_path, TS1)
        with zipfile.ZipFile(hacked_pkg_path, 'a') as z:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                # this would cause a warning from zipfile for duplicate
                # name in zip file (which is perfectly valid, though hacky)
                z.writestr(layouts.Archive.CODE / 'code', 'HACKED')
                z.writestr(layouts.Archive.DATA / 'README', 'HACKED')
        return hacked_pkg_path

    def _pkg_with_history(self, robot, repo, package_name, uuid):
        def make_package(timestamp):
            with TempDir() as tempdir_obj:
                workspace_dir = os.path.join(tempdir_obj.path, package_name)
                ws = Workspace(workspace_dir)
                ws.create(uuid)
                sentinel_file = ws.directory / 'sentinel-{}'.format(timestamp)
                tech.fs.write_file(sentinel_file, timestamp)
                repo.store(ws, timestamp)
                tech.fs.rmtree(workspace_dir)

        with robot.environment:
            make_package(TS1)
            make_package(TS2)
        return package_name

    def pkg_with_history(self, robot, repo):
        return self._pkg_with_history(
            robot, repo, 'pkg_with_history', 'UUID:pkg_with_history')

    def pkg_with_inputs(self, robot, packages, pkg_a, pkg_b):
        inputs = dict(input_a=pkg_a, input_b=pkg_b)
        return self._new_package(robot, packages, 'pkg_with_inputs', inputs)
