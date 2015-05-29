from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase, TempDir
from testtools.content import text_content
from . import ws as m
import fixtures

import contextlib
import os
from ..pkg.workspace import Workspace
from .. import pkg
from .. import db
from .. import tech
from ..translations import add_translation, Peer
Path = tech.fs.Path


@contextlib.contextmanager
def chdir(directory):
    cwd = os.getcwd()
    try:
        os.chdir(directory)
        yield
    finally:
        os.chdir(cwd)


class CaptureStdStream(fixtures.Fixture):

    def __init__(self, stream):
        assert stream.startswith('sys.std')
        super(CaptureStdStream, self).__init__()
        self.stream = stream

    def setUp(self):
        super(CaptureStdStream, self).setUp()
        stdout = self.useFixture(fixtures.StringStream(self.stream)).stream
        self.useFixture(fixtures.MonkeyPatch(self.stream, stdout))

    @property
    def text(self):
        return self.getDetails()[self.stream].as_text()


def CaptureStdout():
    return CaptureStdStream('sys.stdout')


def CaptureStderr():
    return CaptureStdStream('sys.stderr')


class Robot(fixtures.Fixture):
    '''
    Represents a fake user.

    Have a temporary environment with temporary config and working directory.
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
            return Path(os.path.normpath(self.cwd / path))

    def cd(self, dir):
        '''
        Change to directory
        '''
        self.cwd = self._path(dir)
        assert os.path.isdir(self.cwd)

    def ws(self, *args):
        '''
        Imitate calling the ws tool with the given args
        '''
        with fixtures.EnvironmentVariable('HOME', self.home):
            with chdir(self.cwd):
                with CaptureStdout() as stdout, CaptureStderr() as stderr:
                    self.retval = m.cli(self.config_dir, args)
                    self.stdout = stdout.text
                    self.stderr = stderr.text

    def ls(self, directory=None):
        directory = self._path(directory or self.cwd)
        return [
            directory / filename
            for filename in os.listdir(directory)]


class Test_new(TestCase):  # noqa

    def test_first_workspace(self):
        self.given_an_empty_uuid_name_map()
        self.when_new_is_called_with_nonexisting_name()
        self.then_uuid_map_is_created_with_the_uuid_name_stored_in_it()

    def test_new_package_name(self):
        self.given_a_non_empty_uuid_name_map()
        self.when_new_is_called_with_nonexisting_name()
        self.then_workspace_is_created()

    def test_existing_package_name(self):
        self.given_a_non_empty_uuid_name_map()
        self.when_new_is_called_with_already_existing_name()
        self.then_error_is_raised()

    def test_created_workspace_has_same_uuid_as_registered_for_name(self):
        self.given_a_non_empty_uuid_name_map()
        self.when_new_is_called_with_nonexisting_name()
        self.then_workspace_uuid_is_the_uuid_registered_for_name()

    # implementation

    __stderr = None
    __error_raised = False
    home = None
    current_dir = None

    @property
    def personal_id(self):
        return Peer.self().id

    def setUp(self):  # noqa
        super(Test_new, self).setUp()
        # protect user's home directory
        self.home = self.new_temp_home_dir()
        # protect current directory
        self.current_dir = self.new_temp_dir()
        orig_wd = os.getcwd()
        os.chdir(self.current_dir)
        self.addCleanup(os.chdir, orig_wd)

    def given_an_empty_uuid_name_map(self):
        db.connect(db.MEMORY)

    def given_a_non_empty_uuid_name_map(self):
        self.given_an_empty_uuid_name_map()
        add_translation('existing', 'test-uuid')
        self.assertTrue(Peer.self().knows_about('existing'))

    def when_new_is_called_with_nonexisting_name(self):
        m.new(Workspace('new'))

    def when_new_is_called_with_already_existing_name(self):
        self.__stderr = fixtures.StringStream('stderr')
        self.useFixture(self.__stderr)
        self.assertTrue(Peer.self().knows_about('existing'))
        with fixtures.MonkeyPatch('sys.stderr', self.__stderr.stream):
            try:
                m.new(Workspace('existing'))
            except SystemExit:
                self.__error_raised = True

    def then_error_is_raised(self):
        self.assertTrue(self.__error_raised)
        self.__stderr.stream.seek(0)
        self.assertIn('ERROR: ', self.__stderr.stream.read())

    def then_workspace_is_created(self):
        self.assertTrue(Workspace('new').is_valid)

    def then_uuid_map_is_created_with_the_uuid_name_stored_in_it(self):
        self.assertTrue(Peer.self().knows_about('new'))

    def then_workspace_uuid_is_the_uuid_registered_for_name(self):
        self.assertEqual(
            Workspace('new').meta[pkg.metakey.PACKAGE],
            Peer.self().get_translation('new').package_uuid)


class Test_command_line(TestCase):

    # fixtures
    def robot(self):
        return self.useFixture(Robot())

    def ws(self, robot):
        return robot.ws

    def cd(self, robot):
        return robot.cd

    def ls(self, robot):
        return robot.ls

    # tests
    def test(self, robot, ws, cd, ls):
        self.addDetail('home', text_content(robot.home))

        ws('new', 'something')
        self.assertIn('something', robot.stdout)

        cd('something')
        ws('status')
        self.assertIn('no defined inputs', robot.stdout)

        ws('pack')
        package, = ls('temp')

        cd('..')
        ws('develop', 'something-develop', package)
        self.assertIn(robot.cwd / 'something-develop', ls())

        cd('something-develop')
        ws('mount', package, 'older-self')
        ws('status')
        self.assertNotIn('no defined inputs', robot.stdout)
        self.assertIn('older-self', robot.stdout)

        ws('nuke', robot.cwd.parent / 'something')
        ws('nuke')

        cd('..')
        self.assertEqual([], ls(robot.home))
