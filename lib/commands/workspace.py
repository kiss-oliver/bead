from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os

from .. import tech
from ..pkg.workspace import Workspace, CurrentDirWorkspace

from .common import arg, die, warning
from .common import DefaultArgSentinel, PackageReference
from .common import get_channel, opt_workspace
from . import metavar
from . import help
from .. import repos
from ..translations import Peer, add_translation


timestamp = tech.timestamp.timestamp


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


@arg(
    'workspace', type=Workspace, metavar='WORKSPACE',
    help='package and directory to create')
def new(workspace):
    '''
    Create and initialize new workspace directory with a new package.
    '''
    uuid = tech.identifier.uuid()

    assert_may_be_valid_name(workspace.package_name)
    # FIXME: die with message when directory already exists
    add_translation(workspace.package_name, uuid)

    workspace.create(uuid)
    print('Created {}'.format(workspace.package_name))


CURRENT_DIRECTORY = CurrentDirWorkspace()


def arg_workspace_defaulting_to(default_workspace):
    return arg(
        'workspace', nargs='?', type=Workspace, default=default_workspace,
        metavar=metavar.WORKSPACE, help=help.WORKSPACE)


USE_THE_ONLY_REPO = DefaultArgSentinel(
    'if there is exactly one repository,' +
    ' store there, otherwise it MUST be specified')


@arg(
    'repo_name', nargs='?', default=USE_THE_ONLY_REPO, type=str,
    metavar='REPOSITORY', help='Name of repository to store package')
@opt_workspace
def save(repo_name, workspace=CURRENT_DIRECTORY):
    '''
    Save workspace in a repository.
    '''
    assert_valid_workspace(workspace)
    if repo_name is USE_THE_ONLY_REPO:
        repositories = list(repos.get_all())
        if not repositories:
            die('No repositories defined, please define one!')
        if len(repositories) > 1:
            die(
                'REPOSITORY parameter is not optional!\n' +
                '(more than one repositories exists)')
        repo = repositories[0]
    else:
        repo = repos.get(repo_name)
        if repo is None:
            die('Unknown repository: {}'.format(repo_name))
    repo.store(workspace, timestamp())
    print('Successfully stored package.')


DERIVE_FROM_PACKAGE_NAME = DefaultArgSentinel('derive one from package name')


@arg(
    'package_ref', type=PackageReference,
    metavar=metavar.PACKAGE_REF, help=help.PACKAGE_REF)
@arg_workspace_defaulting_to(DERIVE_FROM_PACKAGE_NAME)
def develop(package_ref, workspace):
    '''
    Unpack a package as a source tree.

    Package directory layout is created, but only the source files are
    extracted.
    '''
    try:
        package = package_ref.package
    except LookupError:
        die('Package not found!')
    if not package.is_valid:
        die('Package is found but damaged')
    if workspace is DERIVE_FROM_PACKAGE_NAME:
        workspace = package_ref.default_workspace

    package.unpack_to(workspace)
    assert workspace.is_valid

    print('Extracted source into {}'.format(workspace.directory))
    # XXX: try to load smaller inputs?
    if workspace.inputs:
        print('Input data not loaded, update if needed and load manually')


def assert_valid_workspace(workspace):
    if not workspace.is_valid:
        die('{} is not a valid workspace'.format(workspace.directory))


def indent(lines):
    return ('\t' + line for line in lines)


def _status_version_timestamp(input, peer):
    return (
        'Release time',
        get_channel().get_package(input.package, input.version).timestamp_str)


def get_package_name(package_uuid, peer):
    translations = peer.get_translations(package_uuid)
    if translations:
        return translations[0].name
    raise LookupError(peer.name, package_uuid)


def _status_package_name(input, peer):
    return ('Package name', get_package_name(input.package, peer))


def _status_package_uuid(input, peer):
    return ('Package UUID', input.package)


def _status_version_hash(input, peer):
    return ('Version hash', input.version)


def first(*fields):
    '''
    First available field
    '''
    def field(input, peer):
        for field in fields:
            try:
                return field(input, peer)
            except LookupError:
                pass
        raise LookupError()
    return field


ALL_FIELDS = (
    _status_package_name,
    _status_package_uuid,
    _status_version_timestamp,
    _status_version_hash,
)


DEFAULT_FIELDS = (
    first(_status_package_name, _status_package_uuid),
    first(_status_version_timestamp, _status_version_hash),
)


def format_input(input, peer, fields):
    yield '- {0} (input/{0})'.format(input.name)
    for field in fields:
        try:
            name, value = field(input, peer)
        except LookupError:
            pass
        else:
            yield '\t{}: {}'.format(name, value)


def print_inputs(workspace, peer, fields=ALL_FIELDS):
    assert_valid_workspace(workspace)
    inputs = sorted(workspace.inputs)

    if inputs:
        print('Inputs:')

        input_separator = ''
        for input in inputs:
            print(input_separator, end='')
            print(
                '\n'.join(indent(format_input(input, peer, fields)))
                .expandtabs(2))
            input_separator = os.linesep

        print('')
        unloaded = [
            input.name
            for input in inputs
            if not workspace.is_loaded(input.name)]
        if unloaded:
            print('These inputs are not loaded:')
            unloaded_list = '\t- ' + '\n\t- '.join(unloaded)
            print(unloaded_list.expandtabs(2))
            print('You can "load" or "update" them manually.')


@opt_workspace
@arg('-v', '--verbose', help='show more detailed information')
def status(workspace=CURRENT_DIRECTORY, verbose=False):
    '''
    Show workspace status - name of package, inputs and their unpack status.
    '''
    # TODO: use a template and render it with passing in all data
    peer = Peer.self()
    uuid_needed = verbose
    if workspace.is_valid:
        try:
            package_name = get_package_name(workspace.uuid, peer)
            print('Package Name: {}'.format(package_name))
        except LookupError:
            uuid_needed = True
        if uuid_needed:
            print('Package UUID: {}'.format(workspace.uuid))
        print()
        print_inputs(
            workspace, peer, DEFAULT_FIELDS if not verbose else ALL_FIELDS)
    else:
        warning('Invalid workspace ({})'.format(workspace.directory))


@arg_workspace_defaulting_to(CURRENT_DIRECTORY)
def nuke(workspace):
    '''
    Delete the workspace, inluding data, code and documentation.
    '''
    assert_valid_workspace(workspace)
    directory = workspace.directory
    tech.fs.rmtree(directory)
    print('Deleted workspace {}'.format(directory))
