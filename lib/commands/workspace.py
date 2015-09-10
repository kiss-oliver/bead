from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os

from .. import tech
from ..pkg.workspace import Workspace, CurrentDirWorkspace

from .common import arg, die
from .common import DefaultArgSentinel, PackageReference
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
    'workspace', type=Workspace, metavar=metavar.WORKSPACE,
    help=help.WORKSPACE)
def new(workspace):
    '''
    Create and initialize new workspace.
    '''
    uuid = tech.identifier.uuid()

    assert_may_be_valid_name(workspace.package_name)
    add_translation(workspace.package_name, uuid)

    workspace.create(uuid)
    print('Created {}'.format(workspace.package_name))


CURRENT_DIRECTORY = CurrentDirWorkspace()


def arg_workspace_defaulting_to(default_workspace):
    return arg(
        'workspace', nargs='?', type=Workspace, default=default_workspace,
        metavar=metavar.WORKSPACE, help=help.WORKSPACE)


@arg_workspace_defaulting_to(CURRENT_DIRECTORY)
def pack(workspace):
    '''
    Create a new archive from the workspace.
    '''
    # TODO: #9 personal config: directory to store newly created packages in
    # FIXME: parameter for repo selection in case of multiple repos
    repositories = list(repos.get_all())
    assert len(repositories) == 1, 'Only one repo supported at the moment :('
    repo = repositories[0]
    repo.store(workspace, timestamp())


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
    if workspace is DERIVE_FROM_PACKAGE_NAME:
        workspace = package_ref.default_workspace

    package.unpack_to(workspace)
    assert workspace.is_valid

    print('Extracted source into {}'.format(workspace.directory))
    print_mounts(workspace)


def assert_valid_workspace(workspace):
    if not workspace.is_valid:
        die('{} is not a valid workspace'.format(workspace.directory))


def indent(lines):
    return ('\t' + line for line in lines)


def print_mounts(workspace):
    assert_valid_workspace(workspace)
    inputs = sorted(workspace.inputs)
    if not inputs:
        print('Package has no defined inputs')
    else:
        print('Package inputs:')
        for input in inputs:
            lines = [
                '{}{}:'.format(
                    input.name,
                    '' if workspace.is_mounted(input.name)
                    else ' (not mounted)'),
                '\tpackage: {}'.format(input.package),
                '\tversion: {}'.format(input.version),
            ]
            msg = '\n'.join(indent(lines)).expandtabs(2)
            print('{}'.format(msg))


@arg_workspace_defaulting_to(CURRENT_DIRECTORY)
def status(workspace):
    '''
    Show workspace status - name of package, inputs and their unpack status.
    '''
    # TODO: print Package UUID, version (both hash and timestamp)
    print_mounts(workspace)


@arg_workspace_defaulting_to(CURRENT_DIRECTORY)
def nuke(workspace):
    '''
    Delete the workspace, inluding data, code and documentation.
    '''
    assert_valid_workspace(workspace)
    tech.fs.rmtree(workspace.directory)
