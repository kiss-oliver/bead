from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import contextlib
import os
import fixtures

from . import repos
from . import tech
from .pkg.workspace import Workspace
from .translations import add_translation

from .test import TempDir, CaptureStdout, CaptureStderr
from .tool import ws as m


@contextlib.contextmanager
def chdir(directory):
    cwd = os.getcwd()
    try:
        os.chdir(directory)
        yield
    finally:
        os.chdir(cwd)


class Robot(fixtures.Fixture):
    '''
    Represents a fake user.

    All operations are isolated from the test runner user's environment.
    They work in a dedicated environment with temporary home, config
    and working directories.
    '''

    def setUp(self):
        super(Robot, self).setUp()
        self.base_dir = self.useFixture(TempDir()).path
        os.makedirs(self.home)
        self.cd(self.home)

    def cleanUp(self):
        super(Robot, self).cleanUp()
        self.base_dir = None

    @property
    def config_dir(self):
        return self.base_dir / 'config'

    @property
    def home(self):
        return self.base_dir / 'home'

    def _path(self, path):
        '''
        Convert relative paths to absolute paths
        '''
        if os.path.isabs(path):
            return path
        else:
            return tech.fs.Path(os.path.normpath(self.cwd / path))

    def cd(self, dir):
        '''
        Change to directory
        '''
        self.cwd = self._path(dir)
        assert os.path.isdir(self.cwd)

    def cli(self, *args):
        '''
        Imitate calling the ws tool with the given args
        '''
        with fixtures.EnvironmentVariable('HOME', self.home):
            with chdir(self.cwd):
                with CaptureStdout() as stdout, CaptureStderr() as stderr:
                    try:
                        self.retval = m.cli(self.config_dir, args)
                    except BaseException as e:
                        self.retval = e
                        raise
                    finally:
                        self.stdout = stdout.text
                        self.stderr = stderr.text

    def ls(self, directory=None):
        directory = self._path(directory or self.cwd)
        return [
            directory / filename
            for filename in os.listdir(directory)]

    def write_file(self, path, content):
        assert not os.path.isabs(path)
        tech.fs.write_file(self.cwd / path, content)

    def declare_package(self, name, uuid):
        ''' -> uuid'''
        with fixtures.EnvironmentVariable('HOME', self.home):
            m.initialize_env(self.config_dir)
            add_translation(name, uuid)

    def make_package(self, repo, uuid, timestamp, package_name='test-package'):
        with TempDir() as tempdir_obj:
            workspace_dir = os.path.join(tempdir_obj.path, package_name)
            with fixtures.EnvironmentVariable('HOME', self.home):
                m.initialize_env(self.config_dir)
                ws = Workspace(workspace_dir)
                ws.create(uuid)
                sentinel_file = ws.directory / 'sentinel-{}'.format(timestamp)
                tech.fs.write_file(sentinel_file, timestamp)
                repo.store(ws, timestamp)
                tech.fs.rmtree(workspace_dir)

    def repo(self, name):
        with fixtures.EnvironmentVariable('HOME', self.home):
            m.initialize_env(self.config_dir)
            return repos.get('repo')
