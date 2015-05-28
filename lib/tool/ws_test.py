from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase, TempDir
from . import ws as m
import fixtures

import contextlib
import os
import re
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

    def cd(self, dir):
        '''
        Change to directory
        '''
        if os.path.isabs(dir):
            self.cwd = dir
        else:
            self.cwd = Path(os.path.normpath(self.cwd / dir))
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

    def files(self, pattern='.*'):
        return [
            self.cwd / filename
            for filename in os.listdir(self.cwd)
            if re.match(pattern, filename)]


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
    def alice(self):
        return self.useFixture(Robot())

    def bob(self):
        return self.useFixture(Robot())

    # tests
    def test(self, alice):
        print(alice.home)

        alice.ws('new', 'something')
        print('stdout', alice.stdout)
        print('retval', alice.retval)

        alice.cd('something')
        print(alice.cwd)
        print(alice.files())

        alice.cd('..')
        print(alice.cwd)
        print('files', alice.files())

        alice.ws('nuke', 'something')
        print('files', alice.files())

        # assert False
