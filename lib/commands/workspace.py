from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os

from .. import tech
from ..pkg.workspace import Workspace, CurrentDirWorkspace

from .common import arg, die, opt_workspace
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


DERIVE_FROM_PACKAGE_NAME = DefaultArgSentinel('derive one from package name')


@arg(
    'package_ref', type=PackageReference,
    metavar=metavar.PACKAGE_REF, help=help.PACKAGE_REF)
@arg(
    'workspace', nargs='?', type=Workspace, default=DERIVE_FROM_PACKAGE_NAME,
    metavar=metavar.WORKSPACE, help='workspace directory')
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

    dir = workspace.directory
    print('Extracted source into {}'.format(dir))
    print_mounts(directory=dir)


def assert_valid_workspace(workspace):
    if not workspace.is_valid:
        die('{} is not a valid workspace'.format(workspace.directory))


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


def status():
    '''
    Show workspace status - name of package, mount names and their status.
    '''
    # TODO: print Package UUID
    print_mounts('.')


@arg(
    'workspace', nargs='?', type=Workspace, default=CurrentDirWorkspace(),
    metavar=metavar.WORKSPACE, help=help.WORKSPACE)
def nuke(workspace):
    '''
    Delete the workspace, inluding data, code and documentation.
    '''
    assert_valid_workspace(workspace)
    tech.fs.rmtree(workspace.directory)
