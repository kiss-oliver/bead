from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


from argh.decorators import arg
from ..commands import metavar, help
from ..commands.common import (
    opt_workspace, PackageReference, DefaultArgSentinel, get_channel,
    CurrentDirWorkspace
)
from ..pkg import metakey
from .. import repos


# input_nick
ALL_INPUTS = DefaultArgSentinel('all inputs')
opt_input_nick = arg(
    'input_nick', type=type(''), nargs='?', default=ALL_INPUTS,
    metavar=metavar.INPUT_NICK, help=help.INPUT_NICK)
arg_input_nick = arg(
    'input_nick',
    metavar=metavar.INPUT_NICK, help=help.INPUT_NICK)


# package_ref
NEWEST_VERSION = DefaultArgSentinel('same package, newest version')
# default workspace
CURRENT_DIRECTORY = CurrentDirWorkspace()


@arg_input_nick
@arg(
    'package_ref', type=PackageReference,
    metavar=metavar.PACKAGE_REF, help=help.PACKAGE_MOUNT)
@opt_workspace
def add(input_nick, package_ref, workspace=CURRENT_DIRECTORY):
    '''
    Make data from another package available in the input directory.
    '''
    workspace.mount(input_nick, package_ref.package)
    print(
        '{} mounted on {}.'
        .format(package_ref.package_reference, input_nick))


@arg_input_nick
@opt_workspace
def delete(input_nick, workspace=CURRENT_DIRECTORY):
    '''
    Forget all about input.
    '''
    workspace.delete_input(input_nick)
    print('Input {} is deleted.'.format(input_nick))


@opt_input_nick
@arg(
    'package_ref', type=PackageReference, nargs='?', default=NEWEST_VERSION,
    metavar=metavar.PACKAGE_REF, help=help.PACKAGE_MOUNT)
@opt_workspace
def update(input_nick, package_ref, workspace=CURRENT_DIRECTORY):
    '''
    Update input[s] to newest version or defined package.
    '''
    if input_nick is ALL_INPUTS:
        for input_nick in workspace.inputs:
            _update(workspace, input_nick)
        print('All inputs are up to date.')
    else:
        _update(workspace, input_nick, package_ref)


def _update(workspace, input_nick, package_ref=NEWEST_VERSION):
    spec = workspace.inputspecs[input_nick]
    if package_ref is NEWEST_VERSION:
        uuid = spec[metakey.INPUT_PACKAGE]
        replacement = get_channel().get_package(uuid)
        # XXX: check if found package is newer than currently mounted?
    else:
        replacement = package_ref.package

    workspace.unmount(input_nick)
    workspace.mount(input_nick, replacement)
    print('Mounted {}.'.format(input_nick))


@opt_input_nick
@opt_workspace
def load(input_nick, workspace=CURRENT_DIRECTORY):
    '''
    Put defined input data in place.
    '''
    if input_nick is ALL_INPUTS:
        for input_nick in workspace.inputs:
            _mount(workspace, input_nick)
    else:
        _mount(workspace, input_nick)


def _mount(workspace, input_nick):
    assert workspace.has_input(input_nick)
    if not workspace.is_mounted(input_nick):
        spec = workspace.inputspecs[input_nick]
        uuid = spec[metakey.INPUT_PACKAGE]
        version = spec[metakey.INPUT_VERSION]
        try:
            package = repos.get_package(uuid, version)
        except LookupError:
            print(
                'Could not find archive for {} - not loaded!'
                .format(input_nick))
        else:
            workspace.mount(input_nick, package)
            print('Loaded {}.'.format(input_nick))
    else:
        print('Skipping {} (already loaded)'.format(input_nick))
