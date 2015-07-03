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

from ..pkg.workspace import Workspace
from ..pkg.archive import Archive
from ..pkg import metakey
from .. import db

from .. import PACKAGE, VERSION
from ..translations import Peer, add_translation
from .. import repos


Path = tech.fs.Path
timestamp = tech.timestamp.timestamp

ERROR_EXIT = 1


def opt_workspace(func):
    '''
    Define `workspace` as option, defaulting to current directory
    '''
    decorate = arg(
        '--workspace', dest='workspace_directory', metavar='DIRECTORY',
        default='.',
        help='workspace directory')
    return decorate(func)


def arg_workspace(func):
    '''
    Define `workspace` argument, defaulting to current directory
    '''
    decorate = arg(
        'workspace_directory', nargs='?', metavar='WORKSPACE',
        default='.',
        help='workspace directory')
    return decorate(func)


def arg_new_workspace(func):
    '''
    Define mandatory `workspace` argument (without default)
    '''
    decorate = arg(
        'workspace', type=Workspace,
        help='workspace directory')
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
def pack(workspace_directory='.'):
    '''
    Create a new archive from the workspace
    '''
    # TODO: #9 personal config: directory to store newly created packages in
    workspace = Workspace(workspace_directory)
    repositories = list(repos.get_all())
    assert len(repositories) == 1, 'Only one repo supported at the moment :('
    repo = repositories[0]
    repo.store(workspace, timestamp())


def mount_input_nick(workspace, input_nick):
    assert workspace.has_input(input_nick)
    if not workspace.is_mounted(input_nick):
        spec = workspace.inputspecs[input_nick]
        # TODO: #14 personal config: list of local directories having packages
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
    add_arg = arg(
        'input_nick', metavar=INPUT_NICK_METAVAR, help=INPUT_NICK_HELP)
    return add_arg(func)


@arg(
    'package', metavar='PACKAGE',
    help='package to mount data from')
@arg_input_nick
@opt_workspace
def add_input(input_nick, package, workspace_directory='.'):
    return mount(package, input_nick, workspace_directory)


@arg_input_nick
@arg(
    'package', nargs='?', metavar='PACKAGE',
    help='package to mount data from')
@opt_workspace
def mount(package, input_nick, workspace_directory='.'):
    '''
    Add data from another package to the input directory.
    '''
    workspace = Workspace(workspace_directory)
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


# @command
def status():
    '''
    Show workspace status - name of package, mount names and their status
    '''
    # TODO: print Package UUID
    print_mounts('.')


# @command('input delete')
@arg_input_nick
@opt_workspace
def delete_input(input_nick, workspace_directory='.'):
    '''Forget all about input'''
    workspace = Workspace(workspace_directory)
    workspace.delete_input(input_nick)
    print('Input {} is deleted.'.format(input_nick))


# @command('input update')
@arg(
    'input_nick', metavar=INPUT_NICK_METAVAR, nargs='?', help=INPUT_NICK_HELP)
@arg('package_file_name', metavar='PACKAGE', nargs='?', help='package to load input data from')
@opt_workspace
def update_command(input_nick, package_file_name, workspace_directory='.'):
    '''
    When no input NAME is given, update all inputs to the newest version of the same package.

    When input NAME is given replace that input with a newer version or different package.
    '''
    workspace = Workspace(workspace_directory)
    if input_nick is None:
        update_all_inputs(workspace)
    else:
        update_input(workspace, input_nick, package_file_name)


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
def nuke(workspace_directory):
    '''
    Delete the workspace, inluding data, code and documentation
    '''
    workspace = Workspace(workspace_directory)
    assert_valid_workspace(workspace)
    tech.fs.rmtree(workspace.directory)


def add_repo(name, directory):
    '''
    Define a repository
    '''
    repos.add(name, directory)
    print('Repo "{}" is introduced'.format(name))


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

# TODO: repository management
# - list-repos
# - add-repo repo
# - delete-repo repo-ref
# - set-output-repo repo-ref
# where repo-ref is either an id or its path


def initialize_env(config_dir):
    try:
        os.makedirs(config_dir)
    except OSError:
        assert os.path.isdir(config_dir)
    db_path = os.path.join(config_dir, 'config.sqlite')
    db.connect(db_path)


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
            title='INPUT SUBCOMMAND TITLE',
            help='INPUT SUBCOMMAND HELP',
        ))
    parser.add_commands(
        [
            named('add')(add_repo),
            # list_repos,
            # delete_repo,
            # add_token_to_repo
        ],
        namespace='repo',
        namespace_kwargs=dict(
            title='REPO SUBCOMMAND TITLE',
            help='REPO SUBCOMMAND HELP',
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
