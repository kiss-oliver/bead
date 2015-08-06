from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import appdirs
from argh import ArghParser
from argh.decorators import arg, named

import os
import sys

from .. import tech

from ..pkg.workspace import Workspace, CurrentDirWorkspace
from ..pkg.archive import Archive
from ..pkg import metakey
from .. import db

from .. import PACKAGE, VERSION
from ..translations import Peer, add_translation
from .. import repos


Path = tech.fs.Path
timestamp = tech.timestamp.timestamp

ERROR_EXIT = 1

WORKSPACE_HELP = 'workspace directory'
WORKSPACE_METAVAR = 'DIRECTORY'


def opt_workspace(func):
    '''
    Define `workspace` as option, defaulting to current directory
    '''
    decorate = arg(
        '--workspace', metavar=WORKSPACE_METAVAR,
        type=Workspace, default=CurrentDirWorkspace(),
        help=WORKSPACE_HELP)
    return decorate(func)


def arg_workspace(func):
    '''
    Define `workspace` argument, defaulting to current directory
    '''
    decorate = arg(
        'workspace', nargs='?', metavar=WORKSPACE_METAVAR,
        type=Workspace, default=CurrentDirWorkspace(),
        help=WORKSPACE_HELP)
    return decorate(func)


def arg_new_workspace(func):
    '''
    Define mandatory `workspace` argument (without default)
    '''
    decorate = arg(
        'workspace', type=Workspace, metavar=WORKSPACE_METAVAR,
        help=WORKSPACE_HELP)
    return decorate(func)


def die(msg):
    sys.stderr.write('ERROR: ')
    sys.stderr.write(msg)
    sys.stderr.write('\n')
    sys.exit(ERROR_EXIT)


def assert_valid_workspace(workspace):
    if not workspace.is_valid:
        die('{} is not a valid workspace'.format(workspace.directory))


def assert_may_be_valid_name(name):
    valid_syntax = (
        name
        and os.path.sep not in name
        and '/' not in name
        and '\\' not in name
        and ':' not in name
    )
    if not valid_syntax:
        die('Invalid name "{}"'.format(name))

    if Peer.self().knows_about(name):
        die('"{}" is already used, rename it if you insist'.format(name))


# @command
@arg_new_workspace
def new(workspace):
    '''
    Create new package directory layout.
    '''
    uuid = tech.identifier.uuid()

    assert_may_be_valid_name(workspace.package_name)
    add_translation(workspace.package_name, uuid)

    workspace.create(uuid)
    print('Created {}'.format(workspace.package_name))


# @command
@arg_new_workspace
def develop(workspace, package_file_name, mount=False):
    '''
    Unpack a package as a source tree.

    Package directory layout is created, but only the source files are
    extracted.
    '''
    # TODO: #10 names for packages
    dir = workspace.directory

    package = Archive(package_file_name)
    package.unpack_to(workspace)

    assert workspace.is_valid

    if mount:
        load_inputs(workspace)

    print('Extracted source into {}'.format(dir))
    print_mounts(directory=dir)


# @command
@opt_workspace
def pack(workspace=CurrentDirWorkspace()):
    '''
    Create a new archive from the workspace.
    '''
    # TODO: #9 personal config: directory to store newly created packages in
    repositories = list(repos.get_all())
    assert len(repositories) == 1, 'Only one repo supported at the moment :('
    repo = repositories[0]
    repo.store(workspace, timestamp())


def mount_input_nick(workspace, input_nick):
    assert workspace.has_input(input_nick)
    if not workspace.is_mounted(input_nick):
        spec = workspace.inputspecs[input_nick]
        uuid = spec[metakey.INPUT_PACKAGE]
        version = spec[metakey.INPUT_VERSION]
        for repo in repos.get_all():
            packages = list(repo.find_packages(uuid, version))
            if packages:
                assert len(packages) == 1
                package = packages[0]
                workspace.mount(input_nick, package)
                print('Mounted {}.'.format(input_nick))
                return

        print(
            'Could not find archive for {} - not mounted!'
            .format(input_nick))


# @command('input load')
def load_inputs(workspace):
    '''
    Put all defined input data in place.
    '''
    for input_nick in workspace.inputs:
        mount_input_nick(workspace, input_nick)


def mount_archive(workspace, input_nick, package_file_name):
    assert not workspace.has_input(input_nick)
    workspace.mount(input_nick, Archive(package_file_name))
    print('{} mounted on {}.'.format(package_file_name, input_nick))


INPUT_NICK_HELP = (
    'name of input,'
    + ' its workspace relative location is "input/%(metavar)s"')
INPUT_NICK_METAVAR = 'NAME'


def arg_input_nick(func):
    decorate = arg(
        'input_nick', metavar=INPUT_NICK_METAVAR, help=INPUT_NICK_HELP)
    return decorate(func)


PACKAGE_METAVAR = 'PACKAGE'
PACKAGE_MOUNT_HELP = 'package to mount data from'


@arg('package', metavar=PACKAGE_METAVAR, help=PACKAGE_MOUNT_HELP)
@arg_input_nick
@opt_workspace
def add_input(input_nick, package, workspace=CurrentDirWorkspace()):
    return mount(package, input_nick, workspace)


@arg_input_nick
@arg('package', nargs='?', metavar=PACKAGE_METAVAR, help=PACKAGE_MOUNT_HELP)
@opt_workspace
def mount(package, input_nick, workspace=CurrentDirWorkspace()):
    '''
    Add data from another package to the input directory.
    '''
    # TODO: #10 names for packages
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
        print('Package has no defined inputs')
    else:
        print('Package inputs:')
        for input_nick in sorted(inputs):
            if workspace.is_mounted(input_nick):
                status_msg = 'mounted'
            else:
                status_msg = 'not mounted'
            msg = '  {}: {}'.format(input_nick, status_msg)
            print(msg)


# @command
def status():
    '''
    Show workspace status - name of package, mount names and their status.
    '''
    # TODO: print Package UUID
    print_mounts('.')


# @command('input delete')
@arg_input_nick
@opt_workspace
def delete_input(input_nick, workspace=CurrentDirWorkspace()):
    '''
    Forget all about input.
    '''
    workspace.delete_input(input_nick)
    print('Input {} is deleted.'.format(input_nick))


# @command('input update')
@arg(
    'input_nick', metavar=INPUT_NICK_METAVAR, nargs='?', help=INPUT_NICK_HELP)
@arg('package', metavar=PACKAGE_METAVAR, nargs='?', help=PACKAGE_MOUNT_HELP)
@opt_workspace
def update_command(input_nick, package, workspace=CurrentDirWorkspace()):
    '''
    When no input NAME is given:
        update all inputs to the newest version of all packages.

    When input NAME is given:
        replace that input with a newer version or different package.
    '''
    if input_nick is None:
        update_all_inputs(workspace)
    else:
        update_input(workspace, input_nick, package)


def update_input(workspace, input_nick, package_file_name=None):
    spec = workspace.inputspecs[input_nick]
    if package_file_name:
        newest = Archive(package_file_name)
    else:
        uuid = spec[metakey.INPUT_PACKAGE]
        # find newest package
        newest = None
        for repo in repos.get_all():
            package = repo.find_newest(uuid)
            if package is not None:
                if newest is None or newest.timestamp < package.timestamp:
                    newest = package
        # XXX: check if found package is newer than currently mounted?

    if newest is None:
        print('No package found!!!')
    else:
        workspace.unmount(input_nick)
        workspace.mount(input_nick, newest)
        print('Mounted {}.'.format(input_nick))


def update_all_inputs(workspace):
    for input_nick in workspace.inputs:
        update_input(workspace, input_nick)
    print('All inputs are up to date.')


# @command
@arg_workspace
def nuke(workspace):
    '''
    Delete the workspace, inluding data, code and documentation.
    '''
    assert_valid_workspace(workspace)
    tech.fs.rmtree(workspace.directory)


def add_repo(name, directory):
    '''
    Define a repository.
    '''
    if not os.path.isdir(directory):
        print('ERROR: "{}" is not an existing directory!'.format(directory))
        return
    location = os.path.abspath(directory)
    try:
        repos.add(name, location)
        print('Will remember repo {}'.format(name))
    except ValueError as e:
        print('ERROR:', *e.args)
        print('Check the parameters: both name and directory must be unique!')


def list_repos():
    '''
    List repositories.
    '''
    repositories = repos.get_all()

    def print_repo(repo):
        print('{0.name}: {0.location}'.format(repo))
    try:
        repo = next(repositories)
    except StopIteration:
        print('There are no defined repositories')
    else:
        # XXX use tabulate?
        print('Repositories:')
        print('-------------')
        print_repo(repo)
        for repo in repositories:
            print_repo(repo)


def forget_repo(name):
    '''
    Remove the named repository from the repositories known by the tool.
    '''
    if repos.is_known(name):
        repos.forget(name)
        print('Repository "{}" is forgotten'.format(name))
    else:
        print('WARNING: no repository defined with "{}"'.format(name))


# TODO: names/translations management commands
# - import peer filename
# - rename-peer old-name new-name
# - delete-peer name
#
# - export [--peer name] filename
# - rename-package old-name new-name
# - delete-package package-name
# - lift peer:name [local-name]
#
# TODO: parse package-name
# format: [[peer]:]name[@version]
# already implemented:
# https://gist.github.com/krisztianfekete/25f972c70d1cdbd19b9d#file-new-py


def initialize_env(config_dir):
    try:
        os.makedirs(config_dir)
    except OSError:
        assert os.path.isdir(config_dir)
    db_path = os.path.join(config_dir, 'config.sqlite')
    db.connect(db_path)


INPUT_SUBCOMMAND_TITLE = 'INPUT_SUBCOMMAND_TITLE'
INPUT_SUBCOMMAND_HELP = 'INPUT_SUBCOMMAND_HELP'
REPO_SUBCOMMAND_TITLE = 'REPO_SUBCOMMAND_TITLE'
REPO_SUBCOMMAND_HELP = 'REPO_SUBCOMMAND_HELP'


def make_argument_parser():
    parser = ArghParser(prog=__name__)
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_commands(
        [
            new,
            develop,
            pack,
            mount,
            status,
            named('update')(update_command),
            nuke
        ])
    # FIXME: ArghParser.add_subcommands
    # https://github.com/neithere/argh/issues/88
    parser.add_commands(
        [
            named('load')(load_inputs),
            named('add')(add_input),
            named('delete')(delete_input),
            named('update')(update_command),
        ],
        namespace='input',
        namespace_kwargs=dict(
            title=INPUT_SUBCOMMAND_TITLE,
            help=INPUT_SUBCOMMAND_HELP,
        ))
    parser.add_commands(
        [
            named('add')(add_repo),
            named('list')(list_repos),
            named('forget')(forget_repo),
            # add_token_to_repo
        ],
        namespace='repo',
        namespace_kwargs=dict(
            title=REPO_SUBCOMMAND_TITLE,
            help=REPO_SUBCOMMAND_HELP,
        ))
    return parser


def cli(config_dir, argv):
    initialize_env(config_dir)
    parser = make_argument_parser()
    parser.dispatch(argv)
    # TODO verify exit status


def main():
    config_dir = appdirs.user_config_dir(
        PACKAGE + '-6a4d9d98-8e64-4a2a-b6c2-8a753ea61daf')
    cli(config_dir, sys.argv[1:])


if __name__ == '__main__':
    main()
