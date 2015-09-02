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
from ..pkg.spec import parse as parse_package_spec
from ..pkg import metakey
from .. import db

from .. import PACKAGE, VERSION
from ..translations import Peer, add_translation
from .. import repos
from .. import channels


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


def get_channel():
    return channels.AllAvailable(repos.get_all())


class PackageReference(object):
    def __init__(self, package_reference):
        self.package_reference = package_reference

    @property
    def package(self):
        if os.path.isfile(self.package_reference):
            return Archive(self.package_reference)

        package_spec = parse_package_spec(self.package_reference)
        peer = Peer.by_name(package_spec.peer)
        package_translation = peer.get_translation(package_spec.name)
        uuid = package_translation.package_uuid
        package = (
            get_channel()
            .get_package(uuid, package_spec.version, package_spec.offset))
        return package

    @property
    def default_workspace(self):
        if os.path.isfile(self.package_reference):
            archive_filename = os.path.basename(self.package_reference)[0]
            workspace_dir = os.path.splitext(archive_filename)
        else:
            package_spec = parse_package_spec(self.package_reference)
            workspace_dir = package_spec.name
        return Workspace(workspace_dir)


PACKAGE_REF_HELP = (
    'either an archive file name or' +
    ' a reference the format peer:package_name@version-offset' +
    ' where every part except package_name is optional')
PACKAGE_REF_METAVAR = 'PACKAGE'

arg_package_ref = arg(
    'package_ref', type=PackageReference,
    metavar=PACKAGE_REF_METAVAR, help=PACKAGE_REF_HELP)


class DefaultArgSentinel(object):
    '''
    I am a sentinel for @argh.arg default values.

    I.e. I can tell you, that you got the default value.

    I also provide sensible description for the default value.
    '''

    def __init__(self, description):
        self.description = description

    def __repr__(self):
        return self.description

DERIVE_FROM_PACKAGE_NAME = DefaultArgSentinel('derive from package name')


# @command
@arg(
    'workspace', nargs='?', type=Workspace, default=DERIVE_FROM_PACKAGE_NAME,
    metavar=WORKSPACE_METAVAR, help='workspace directory')
@arg_package_ref
def develop(package_ref, workspace, mount=False):
    '''
    Unpack a package as a source tree.

    Package directory layout is created, but only the source files are
    extracted.
    '''
    try:
        package = package_ref.package
    except LookupError:
        die('Package not found!')
    if workspace is DERIVE_FROM_PACKAGE_NAME:
        workspace = package_ref.default_workspace

    package.unpack_to(workspace)
    assert workspace.is_valid

    if mount:
        load_inputs(workspace)

    dir = workspace.directory
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
        try:
            package = repos.get_package(uuid, version)
        except LookupError:
            print(
                'Could not find archive for {} - not mounted!'
                .format(input_nick))
        else:
            workspace.mount(input_nick, package)
            print('Mounted {}.'.format(input_nick))


# @command('input load')
def load_inputs(workspace):
    '''
    Put all defined input data in place.
    '''
    for input_nick in workspace.inputs:
        mount_input_nick(workspace, input_nick)


INPUT_NICK_HELP = (
    'name of input,'
    + ' its workspace relative location is "input/%(metavar)s"')
INPUT_NICK_METAVAR = 'NAME'


def arg_input_nick(func):
    decorate = arg(
        'input_nick', metavar=INPUT_NICK_METAVAR, help=INPUT_NICK_HELP)
    return decorate(func)


# FIXME: unused???
PACKAGE_METAVAR = 'PACKAGE'
PACKAGE_MOUNT_HELP = 'package to mount data from'


@arg_package_ref
@arg_input_nick
@opt_workspace
def add_input(input_nick, package_ref, workspace=CurrentDirWorkspace()):
    '''
    Add data from another package to the input directory.
    '''
    return mount(package_ref, input_nick, workspace)


ALREADY_CONFIGURED_PACKAGE = DefaultArgSentinel(
    'already configured package for {}'
    .format(INPUT_NICK_METAVAR))


@arg_input_nick
@arg(
    'package_ref', type=PackageReference, nargs='?',
    default=ALREADY_CONFIGURED_PACKAGE,
    metavar=PACKAGE_REF_METAVAR, help=PACKAGE_REF_HELP)
@opt_workspace
def mount(package_ref, input_nick, workspace=CurrentDirWorkspace()):
    '''
    Add data from another package to the input directory.
    '''
    if package_ref is ALREADY_CONFIGURED_PACKAGE:
        mount_input_nick(workspace, input_nick)
    else:
        assert not workspace.has_input(input_nick)
        workspace.mount(input_nick, package_ref.package)
        print(
            '{} mounted on {}.'
            .format(package_ref.package_reference, input_nick))


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


ALL_INPUTS = DefaultArgSentinel('all inputs')
NEWEST_VERSION = DefaultArgSentinel('same package, newest version')


# @command('input update')
@arg(
    'input_nick', type=type(''), nargs='?', default=ALL_INPUTS,
    metavar=INPUT_NICK_METAVAR, help=INPUT_NICK_HELP)
@arg(
    'package_ref', type=PackageReference, nargs='?',
    default=NEWEST_VERSION,
    metavar=PACKAGE_REF_METAVAR, help=PACKAGE_REF_HELP)
@opt_workspace
def update_command(input_nick, package_ref, workspace=CurrentDirWorkspace()):
    '''
    When no input NAME is given:
        update all inputs to the newest version of all packages.

    When input NAME is given:
        replace that input with a newer version or different package.
    '''
    if input_nick is ALL_INPUTS:
        for input_nick in workspace.inputs:
            update_input(workspace, input_nick)
        print('All inputs are up to date.')
    else:
        update_input(workspace, input_nick, package_ref)


def update_input(workspace, input_nick, package_ref=NEWEST_VERSION):
    spec = workspace.inputspecs[input_nick]
    if package_ref is NEWEST_VERSION:
        uuid = spec[metakey.INPUT_PACKAGE]
        replacement = get_channel().get_package(uuid)
        # XXX: check if found package is newer than currently mounted?
    else:
        replacement = package_ref.package

    if replacement is None:
        print('No package found!!!')
    else:
        workspace.unmount(input_nick)
        workspace.mount(input_nick, replacement)
        print('Mounted {}.'.format(input_nick))


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
            nuke,
            # TODO: #10 names for packages
            # rename  # package
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
            # TODO: rename repo
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
