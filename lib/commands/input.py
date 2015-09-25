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
    metavar=metavar.PACKAGE_REF, help=help.PACKAGE_LOAD)
@opt_workspace
def add(input_nick, package_ref, workspace=CURRENT_DIRECTORY):
    '''
    Make data from another package available in the input directory.
    '''
    workspace.load(input_nick, package_ref.package)
    print(
        '{} loaded on {}.'
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
    metavar=metavar.PACKAGE_REF, help=help.PACKAGE_LOAD)
@opt_workspace
def update(input_nick, package_ref, workspace=CURRENT_DIRECTORY):
    '''
    Update input[s] to newest version or defined package.
    '''
    if input_nick is ALL_INPUTS:
        for input in workspace.inputs:
            _update(workspace, input)
        print('All inputs are up to date.')
    else:
        _update(workspace, workspace.get_input(input_nick), package_ref)


def _update(workspace, input, package_ref=NEWEST_VERSION):
    if package_ref is NEWEST_VERSION:
        replacement = get_channel().get_package(input.package)
        # XXX: check if found package is newer than currently loaded?
    else:
        replacement = package_ref.package

    if workspace.is_loaded(input.name):
        workspace.unload(input.name)
    workspace.load(input.name, replacement)
    print('Loaded {}.'.format(input.name))


@opt_input_nick
@opt_workspace
def load(input_nick, workspace=CURRENT_DIRECTORY):
    '''
    Put defined input data in place.
    '''
    if input_nick is ALL_INPUTS:
        for input in workspace.inputs:
            _load(workspace, input)
    else:
        _load(workspace, workspace.get_input(input_nick))


def _load(workspace, input):
    assert input is not None
    if not workspace.is_loaded(input.name):
        try:
            package = repos.get_package(input.package, input.version)
        except LookupError:
            print(
                'Could not find archive for {} - not loaded!'
                .format(input.name))
        else:
            workspace.load(input.name, package)
            print('Loaded {}.'.format(input.name))
    else:
        print('Skipping {} (already loaded)'.format(input.name))
