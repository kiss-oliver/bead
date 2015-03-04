from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from mando.core import Program

from abc import ABCMeta, abstractmethod
import os
import sys

from .. import config
from .. import tech

from ..pkg.workspace import Workspace
from ..pkg import archive
from ..pkg import layouts
from ..pkg import metakey

from .. import VERSION

# TODO: consider using argparse directly (or argh?)
# Reasons:
#   - validate/create missing user config before all commands
#   - one place to look for implemented commands

main = Program('ws', VERSION)
arg = main.arg
command = main.command

Path = tech.fs.Path
timestamp = tech.timestamp.timestamp
uuid_translator = tech.uuid_translator.uuid_translator

ERROR_EXIT = 1


def die(msg):
    sys.stderr.write('ERROR: ')
    sys.stderr.write(msg)
    sys.stderr.write('\n')
    sys.exit(ERROR_EXIT)


def assert_valid_workspace(workspace):
    if not workspace.is_valid:
        die('{} is not a valid workspace'.format(workspace.directory))


def assert_may_be_valid_name(cfg, name):
    valid_syntax = (
        name
        and os.path.sep not in name
        and '/' not in name
        and '\\' not in name
        and ':' not in name
    )
    if not valid_syntax:
        die('Invalid name "{}"'.format(name))

    packages_db_file_name = cfg.path_to(config.PACKAGES_DB_FILE_NAME)
    with uuid_translator(packages_db_file_name) as t:
        if t.has_name(scope=cfg.personal_id, name=name):
            die('"{}" is already used, rename it if you insist'.format(name))


@command
def new(name):
    '''
    Create new package directory layout.
    '''
    cfg = config.Config()
    assert_may_be_valid_name(cfg, name)

    package_uuid = tech.identifier.uuid()
    packages_db_file_name = cfg.path_to(config.PACKAGES_DB_FILE_NAME)
    ws = Workspace(name)
    ws.create(package_uuid)
    with uuid_translator(packages_db_file_name) as t:
        t.add(scope=cfg.personal_id, name=name, uuid=package_uuid)

    print('Created {}'.format(name))


class Package(object):
    '''
    I am providing high-level access to a content of a data package.
    '''

    __metaclass__ = ABCMeta

    package_uuid = str
    version = str
    timestamp_str = str

    @abstractmethod
    def export(self, exported_archive_path):
        '''
        I pack my content (everything!) as a zip-Archive to requested location.
        '''
        pass

    def unpack_to(self, workspace):
        self.unpack_code_to(workspace.directory)
        workspace.create_directories()
        self.unpack_meta_to(workspace)

    @abstractmethod
    def unpack_data_to(self, path):
        pass

    @abstractmethod
    def unpack_code_to(self, path):
        pass

    @abstractmethod
    def unpack_meta_to(self, workspace):
        pass


class ArchivePackage(Package):
    '''
    I am providing high-level access to a content of an Archive.
    '''

    def __init__(self, archive_path):
        self.__archive_path = archive_path
        with self.archive as archive:
            self.package_uuid = archive.uuid
            self.version = archive.version
            self.timestamp_str = archive.meta[metakey.PACKAGE_TIMESTAMP]

    @property
    def archive(self):
        return archive.Archive(self.__archive_path)

    def export(self, exported_archive_path):
        pass

    def unpack_data_to(self, path):
        pass

    def unpack_code_to(self, path):
        with self.archive as archive:
            archive.extract_code_to(path)

    def unpack_meta_to(self, workspace):
        with self.archive as archive:
            workspace.meta = archive.meta

    def unpack_to(self, workspace):
        # FIXME: unpack_to is not expected to be replaced
        super(ArchivePackage, self).unpack_to(workspace)
        # this flat repo can be used to mount packages for demo purposes
        # that is, until we have a proper repo
        workspace.flat_repo = os.path.abspath(
            os.path.dirname(self.__archive_path)
        )


class Repository(object):

    def find_package(self, package_uuid, version=None):
        # -> [Package]
        pass

    def find_newest(self, package_uuid):
        # -> Package
        pass

    def store(self, workspace, timestamp):
        # -> Package
        pass


class UserManagedDirectory(Repository):
    pass


@command
def develop(name, package_file_name, mount=False):
    '''
    Unpack a package as a source tree.

    Package directory layout is created, but only the source files are
    extracted.
    '''
    # TODO: #10 names for packages
    dir = Path(name)
    workspace = Workspace(dir)
    package = ArchivePackage(package_file_name)
    package.unpack_to(workspace)

    assert workspace.is_valid

    if mount:
        mount_all(workspace)

    print('Extracted source into {}'.format(dir))
    print_mounts(directory=dir)


@command
def pack():
    '''Create a new archive from the workspace'''
    # TODO: #9 personal config: directory to store newly created packages in
    # repo = get_store_repo()
    # repo.store_workspace(Workspace(), timestamp())
    workspace = Workspace()
    ts = timestamp()
    zipfilename = (
        Path('.') / layouts.Workspace.TEMP / (
            '{package}_{timestamp}.zip'
            .format(
                package=workspace.package_name,
                timestamp=ts,
            )
        )
    )
    workspace.pack(zipfilename, timestamp=ts)

    print('Package created at {}'.format(zipfilename))


def find_package(repo_dir, package_uuid, package_version):
    # TODO: #14 personal config: list of local directories having packages
    for name in os.listdir(repo_dir):
        candidate = repo_dir / name
        try:
            package = archive.Archive(candidate)
            if package.uuid == package_uuid:
                if package.version == package_version:
                    return candidate
        except:
            pass


def mount_input_nick(workspace, input_nick):
    assert workspace.has_input(input_nick)
    if not workspace.is_mounted(input_nick):
        spec = workspace.inputspecs[input_nick]
        package_file_name = find_package(
            Path(workspace.flat_repo),
            spec[metakey.INPUT_PACKAGE],
            spec[metakey.INPUT_VERSION],
        )
        if package_file_name is None:
            print(
                'Could not find archive for {} - not mounted!'
                .format(input_nick)
            )
            return
        workspace.mount(input_nick, archive.Archive(package_file_name))
        print('Mounted {}.'.format(input_nick))


@command('mount-all')
def mount_all(workspace):
    for input_nick in workspace.inputs:
        mount_input_nick(workspace, input_nick)


def mount_archive(workspace, input_nick, package_file_name):
    assert not workspace.has_input(input_nick)
    workspace.mount(input_nick, archive.Archive(package_file_name))
    print('{} mounted on {}.'.format(package_file_name, input_nick))


@command
@arg(
    'package', nargs='?', metavar='PACKAGE',
    help='package to mount data from'
)
@arg(
    'input_nick', metavar='NAME',
    help='data will be mounted under "input/%(metavar)s"'
)
def mount(package, input_nick):
    '''
    Add data from another package to the input directory.
    '''
    # TODO: #10 names for packages
    workspace = Workspace()
    if package is None:
        mount_input_nick(workspace, input_nick)
    else:
        package_file_name = package
        mount_archive(workspace, input_nick, package_file_name)


def print_mounts(directory):
    workspace = Workspace(directory)
    assert_valid_workspace(workspace)
    inputs = workspace.inputs
    if not inputs:
        print('Package has no defined inputs, yet')
    else:
        print('Package inputs:')
        msg_mounted = 'mounted'
        msg_not_mounted = 'not mounted'
        for input_nick in sorted(inputs):
            print(
                '  {}: {}'
                .format(
                    input_nick,
                    msg_mounted
                    if workspace.is_mounted(input_nick)
                    else msg_not_mounted
                )
            )


@command
def status():
    '''Show workspace status - name of package, mount names and their status'''
    # TODO: print Package UUID
    print_mounts('.')


@command('delete-input')
def delete_input(input_nick):
    '''Forget input'''
    Workspace().delete_input(input_nick)
    print('Input {} is deleted.'.format(input_nick))


@command
@arg('package_file_name', nargs='?')
def update(input_nick, package_file_name):
    '''Replace input with a newer version or different package.
    '''
    # TODO: #16 implement update command
    pass


@command
@arg(
    'directory', nargs='?', default='.',
    help='workspace directory (default: %(default)s)'
)
def nuke(directory):
    '''Delete the workspace, inluding data, code and documentation'''
    workspace = Workspace(directory)
    assert_valid_workspace(workspace)
    tech.fs.rmtree(os.path.abspath(directory))

# TODO: rename commands
# input add <name> (<package>|<file>)
# input load <name>
# input load --all
# input delete <name>
