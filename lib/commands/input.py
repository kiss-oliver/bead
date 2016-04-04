from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


from argh.decorators import arg
from ..commands import arg_metavar
from ..commands import arg_help
from ..commands.common import (
    opt_workspace, DefaultArgSentinel,
    CurrentDirWorkspace,
    die, warning
)
from ..pkg.spec import PackageQuery
from ..commands.common import package_spec_kwargs, get_package_ref
from .. import repos


# input_nick
ALL_INPUTS = DefaultArgSentinel('all inputs')
opt_input_nick = arg(
    'input_nick', type=type(''), nargs='?', default=ALL_INPUTS,
    metavar=arg_metavar.INPUT_NICK, help=arg_help.INPUT_NICK)
arg_input_nick = arg(
    'input_nick',
    metavar=arg_metavar.INPUT_NICK, help=arg_help.INPUT_NICK)


# package_ref
NEWEST_VERSION = DefaultArgSentinel('same package, newest version')
USE_INPUT_NICK = DefaultArgSentinel('use {}'.format(arg_metavar.INPUT_NICK))
# default workspace
CURRENT_DIRECTORY = CurrentDirWorkspace()


@package_spec_kwargs
@arg(
    'package_name', metavar=arg_metavar.PACKAGE_REF, nargs='?', type=str,
    default=USE_INPUT_NICK,
    help=arg_help.PACKAGE_LOAD)
@arg_input_nick
@opt_workspace
def add(input_nick, package_name, workspace=CURRENT_DIRECTORY, **kwargs):
    '''
    Make data from another package available in the input directory.
    '''
    # assert False, vars()
    if package_name is USE_INPUT_NICK:
        package_name = input_nick
    package_ref = get_package_ref(package_name, kwargs)
    try:
        package = package_ref.package
    except LookupError:
        die('Not a known package name: {}'.format(package_name))

    _check_load_with_feedback(
        workspace, input_nick, package, package_name)


@arg_input_nick
@opt_workspace
def delete(input_nick, workspace=CURRENT_DIRECTORY):
    '''
    Forget all about input.
    '''
    workspace.delete_input(input_nick)
    print('Input {} is deleted.'.format(input_nick))


@package_spec_kwargs
@arg(
    'package_ref', metavar=arg_metavar.PACKAGE_REF, nargs='?', type=str,
    default=NEWEST_VERSION,
    help=arg_help.PACKAGE_LOAD)
@opt_input_nick
@opt_workspace
def update(input_nick, package_ref, workspace=CURRENT_DIRECTORY, **kwargs):
    '''
    Update input[s] to newest version or defined package.
    '''
    if input_nick is ALL_INPUTS:
        for input in workspace.inputs:
            _update(workspace, input)
        print('All inputs are up to date.')
    else:
        # FIXME: update: fix to allow to select previous/next/closest to a timestamp package
        if package_ref is not NEWEST_VERSION:
            package_ref = get_package_ref(package_ref, kwargs)
        _update(workspace, workspace.get_input(input_nick), package_ref)


def _update(workspace, input, package_ref=NEWEST_VERSION):
    if package_ref is NEWEST_VERSION:
        # FIXME: input._update
        query = (
            PackageQuery()
            .by_uuid(input.package)
            .is_newer_than(input.timestamp)
            .keep_newest())
        replacement = next(query.get_packages(repos.env.get_repos()))
    else:
        replacement = package_ref.package

    _check_load_with_feedback(workspace, input.name, replacement)


@opt_input_nick
@opt_workspace
def load(input_nick, workspace=CURRENT_DIRECTORY):
    '''
    Put defined input data in place.
    '''
    if input_nick is ALL_INPUTS:
        inputs = workspace.inputs
        if inputs:
            for input in inputs:
                _load(workspace, input)
        else:
            warning('No inputs defined to load.')
    else:
        _load(workspace, workspace.get_input(input_nick))


def _load(workspace, input):
    assert input is not None
    if not workspace.is_loaded(input.name):
        try:
            package = repos.get_package(input.package, input.version)
        except LookupError:
            warning(
                'Could not find archive for {} - not loaded!'
                .format(input.name))
        else:
            _check_load_with_feedback(workspace, input.name, package)
    else:
        print('Skipping {} (already loaded)'.format(input.name))


def _check_load_with_feedback(
        workspace, input_name, package, package_name=None):
    if package.is_valid:
        if workspace.is_loaded(input_name):
            workspace.unload(input_name)
        workspace.load(input_name, package)
        if package_name:
            print('{} loaded on {}.'.format(package_name, input_name))
        else:
            print('Loaded {}.'.format(input_name))
    else:
        warning(
            'Package for {} is found but damaged - not loading.'
            .format(input_name))
