from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase, TempDir
# from ..test import xfail
from testtools.content import text_content
from testtools.matchers import FileContains, Not, Contains, FileExists
from . import ws as m
import fixtures

import contextlib
import os
from ..pkg.workspace import Workspace
from .. import commands
from .. import pkg
from .. import repos
from .. import db
from .. import tech
from ..translations import add_translation, Peer
Path = tech.fs.Path
timestamp = tech.timestamp.timestamp


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

    def make_package(self, repo, uuid, timestamp):
        with TempDir() as tempdir_obj:
            tempdir = tempdir_obj.path
            with fixtures.EnvironmentVariable('HOME', self.home):
                m.initialize_env(self.config_dir)
                ws = Workspace(tempdir)
                ws.create(uuid)
                sentinel_file = ws.directory / 'sentinel-{}'.format(timestamp)
                tech.fs.write_file(sentinel_file, timestamp)
                repo.store(ws, timestamp)
                tech.fs.rmtree(tempdir)

    def repo(self, name):
        with fixtures.EnvironmentVariable('HOME', self.home):
            m.initialize_env(self.config_dir)
            return repos.get('repo')


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
        with CaptureStdout():
            commands.workspace.new(Workspace('new'))

    def when_new_is_called_with_already_existing_name(self):
        self.__stderr = fixtures.StringStream('stderr')
        self.useFixture(self.__stderr)
        self.assertTrue(Peer.self().knows_about('existing'))
        with fixtures.MonkeyPatch('sys.stderr', self.__stderr.stream):
            try:
                commands.workspace.new(Workspace('existing'))
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


class Test_basic_command_line(TestCase):

    # fixtures
    def robot(self):
        return self.useFixture(Robot())

    def ws(self, robot):
        return robot.ws

    def cd(self, robot):
        return robot.cd

    def ls(self, robot):
        return robot.ls

    def repo_dir(self):
        return self.new_temp_dir()

    # tests
    def test(self, robot, ws, cd, ls, repo_dir):
        self.addDetail('home', text_content(robot.home))

        ws('new', 'something')
        self.assertIn('something', robot.stdout)

        cd('something')
        ws('status')
        self.assertIn('no defined inputs', robot.stdout)

        ws('repo', 'add', 'default', repo_dir)
        ws('pack')

        cd('..')
        ws('develop', 'something', 'something-develop')
        self.assertIn(robot.cwd / 'something-develop', ls())

        cd('something-develop')
        ws('input', 'add', 'older-self', 'something')
        ws('status')
        self.assertNotIn('no defined inputs', robot.stdout)
        self.assertIn('older-self', robot.stdout)

        ws('nuke', robot.cwd.parent / 'something')
        ws('nuke')

        cd('..')
        self.assertEqual([], ls(robot.home))


class Test_shared_repo(TestCase):

    # fixtures
    def repo(self):
        return self.new_temp_dir()

    def timestamp(self):
        return timestamp()

    def package(self, timestamp):
        tmp = self.new_temp_dir()
        ws = Workspace(tmp / 'ws')
        ws.create('pkg-uuid')
        package_archive = tmp / 'package.zip'
        ws.pack(package_archive, timestamp)
        return package_archive

    def alice(self, repo):
        robot = self.useFixture(Robot())
        robot.ws('repo', 'add', 'bobrepo', repo)
        return robot

    def bob(self, repo):
        robot = self.useFixture(Robot())
        robot.ws('repo', 'add', 'alicerepo', repo)
        return robot

    # tests
    def test_update(self, alice, bob, package):
        bob.ws('new', 'bobpkg')
        bob.cd('bobpkg')
        bob.ws('input', 'add', 'alicepkg1', package)
        bob.ws('input', 'add', 'alicepkg2', package)

        alice.ws('develop', package, 'alicepkg')
        alice.cd('alicepkg')
        alice.ls()
        alice.write_file('output/datafile', '''Alice's new data''')
        alice.ws('pack')

        # update only one input
        bob.ws('input', 'update', 'alicepkg1')

        self.assertThat(
            bob.cwd / 'input/alicepkg1/datafile',
            FileContains('''Alice's new data'''))

        # second input directory not changed
        self.assertThat(
            bob.cwd / 'input/alicepkg2/datafile',
            Not(FileExists()))

        # update all inputs
        bob.ws('input', 'update')

        self.assertThat(
            bob.cwd / 'input/alicepkg2/datafile',
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
        robot.ws('repo', 'list')
        self.assertThat(
            robot.stdout, Contains('There are no defined repositories'))

    def test_add_non_existing_directory_fails(self, robot):
        robot.ws('repo', 'add', 'notadded', 'non-existing')
        self.assertThat(robot.stdout, Contains('ERROR'))
        self.assertThat(robot.stdout, Not(Contains('notadded')))

    def test_add_multiple(self, robot, dir1, dir2):
        robot.ws('repo', 'add', 'name1', 'dir1')
        robot.ws('repo', 'add', 'name2', 'dir2')
        self.assertThat(robot.stdout, Not(Contains('ERROR')))

        robot.ws('repo', 'list')
        self.assertThat(robot.stdout, Contains('name1'))
        self.assertThat(robot.stdout, Contains('name2'))
        self.assertThat(robot.stdout, Contains('dir1'))
        self.assertThat(robot.stdout, Contains('dir2'))

    def test_add_with_same_name_fails(self, robot, dir1, dir2):
        robot.ws('repo', 'add', 'name', 'dir1')
        self.assertThat(robot.stdout, Not(Contains('ERROR')))

        robot.ws('repo', 'add', 'name', 'dir2')
        self.assertThat(robot.stdout, Contains('ERROR'))

    def test_add_same_directory_twice_fails(self, robot, dir1):
        robot.ws('repo', 'add', 'name1', dir1)
        self.assertThat(robot.stdout, Not(Contains('ERROR')))

        robot.ws('repo', 'add', 'name2', dir1)
        self.assertThat(robot.stdout, Contains('ERROR'))

    def test_forget_repo(self, robot, dir1, dir2):
        robot.ws('repo', 'add', 'repo-to-delete', dir1)
        robot.ws('repo', 'add', 'another-repo', dir2)

        robot.ws('repo', 'forget', 'repo-to-delete')
        self.assertThat(robot.stdout, Contains('forgotten'))

        robot.ws('repo', 'list')
        self.assertThat(robot.stdout, Not(Contains('repo-to-delete')))
        self.assertThat(robot.stdout, Contains('another-repo'))

    def test_forget_nonexisting_repo(self, robot):
        robot.ws('repo', 'forget', 'non-existing')
        self.assertThat(robot.stdout, Contains('WARNING'))


# timestamps
TS1 = '20150901_151015_1'
TS2 = '20150901_151016_2'


class Test_package_references(TestCase):

    # fixtures
    def _robot(self):
        return self.useFixture(Robot())

    def repo(self, _robot):
        robot = _robot
        repo_dir = robot.cwd / 'repo'
        os.makedirs(repo_dir)
        robot.ws('repo', 'add', 'repo', repo_dir)
        return robot.repo('repo')

    def robot(self, _robot, repo):
        '''
        I am a robot user with a repo
        '''
        return _robot

    def pkg_a(self, robot):
        package_name = 'pkg_a'
        robot.ws('new', package_name)
        robot.cd(package_name)
        robot.write_file('something', package_name)
        robot.ws('pack')
        robot.cd('..')
        robot.ws('nuke', package_name)
        return package_name

    def pkg_with_history(self, robot, repo):
        robot.declare_package('pkg_with_history', 'UUID')
        robot.make_package(repo, 'UUID', TS1)
        robot.make_package(repo, 'UUID', TS2)

    # tests
    def test_develop_by_name(self, robot, pkg_a):
        robot.ws('develop', pkg_a)

        self.assertTrue(Workspace(robot.cwd / pkg_a).is_valid)
        self.assertThat(robot.cwd / pkg_a / 'something', FileContains(pkg_a))

    def test_develop_missing_package(self, robot, pkg_a):
        robot.ws('repo', 'forget', 'repo')
        try:
            robot.ws('develop', pkg_a)
        except SystemExit:
            self.assertThat(robot.stderr, Contains('Package'))
            self.assertThat(robot.stderr, Contains('not found'))
        else:
            self.fail('develop should have exited on missing package')

    def assert_develop_version(self, robot, pkg_spec, timestamp):
        assert pkg_spec.startswith('pkg_with_history')
        robot.ws('develop', pkg_spec)
        self.assertThat(
            robot.cwd / 'pkg_with_history' / 'sentinel-' + timestamp,
            FileExists())

    def test_develop_without_version(self, robot, pkg_with_history):
        self.assert_develop_version(robot, 'pkg_with_history', TS2)

    def test_develop_without_offset(self, robot, pkg_with_history):
        self.assert_develop_version(robot, 'pkg_with_history@', TS2)

    def test_develop_with_offset(self, robot, pkg_with_history):
        self.assert_develop_version(robot, 'pkg_with_history@-1', TS1)

    def test_develop_w_version_wo_offset(self, robot, pkg_with_history):
        self.assert_develop_version(robot, 'pkg_with_history@' + TS1, TS1)

    def test_develop_available_matches_to_version_are_less_than_offset(
            self, robot, pkg_with_history):
        self.assert_develop_version(
            robot, 'pkg_with_history@{}-1'.format(TS2), TS2)
