from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from cliscape import Command

from ..commands import arg_metavar
from ..commands import arg_help
from ..commands.common import (
    OPTIONAL_WORKSPACE, DefaultArgSentinel,
    CurrentDirWorkspace,
    die, warning
)
from ..pkg.spec import PackageQuery
from ..commands.common import package_spec_kwargs, get_package_ref
from .. import repos


# input_nick
ALL_INPUTS = DefaultArgSentinel('all inputs')
def OPTIONAL_INPUT_NICK(parser):
    '''
    Declare `input_nick` as optional parameter
    '''
    parser.arg(
        'input_nick', type=type(''), nargs='?', default=ALL_INPUTS,
        metavar=arg_metavar.INPUT_NICK, help=arg_help.INPUT_NICK)
def MANDATORY_INPUT_NICK(parser):
    '''
    Declare `input_nick` as mandatory parameter
    '''
    parser.arg(
        'input_nick',
        metavar=arg_metavar.INPUT_NICK, help=arg_help.INPUT_NICK)


# package_ref
NEWEST_VERSION = DefaultArgSentinel('same package, newest version')
USE_INPUT_NICK = DefaultArgSentinel('use {}'.format(arg_metavar.INPUT_NICK))
# default workspace
CURRENT_DIRECTORY = CurrentDirWorkspace()


class CmdAdd(Command):
    '''
    Make data from another package available in the input directory.
    '''

    def arguments(self, arg):
        arg(package_spec_kwargs)
        arg('package_name', metavar=arg_metavar.PACKAGE_REF, nargs='?', type=str,
            default=USE_INPUT_NICK,
            help=arg_help.PACKAGE_LOAD)
        arg(MANDATORY_INPUT_NICK)
        arg(OPTIONAL_WORKSPACE)

    def run(self, args):
        input_nick = args.input_nick
        package_name = args.package_name
        workspace = args.workspace
        kwargs = dict(args.query or {})
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


class CmdDelete(Command):
    '''
    Forget all about an input.
    '''

    def arguments(self, arg):
        arg(MANDATORY_INPUT_NICK)
        arg(OPTIONAL_WORKSPACE)

    def run(self, args):
        input_nick = args.input_nick
        workspace = args.workspace
        workspace.delete_input(input_nick)
        print('Input {} is deleted.'.format(input_nick))


class CmdUpdate(Command):
    '''
    Update input[s] to newest version or defined package.
    '''

    def arguments(self, arg):
        arg(package_spec_kwargs)
        arg(
            'package_ref', metavar=arg_metavar.PACKAGE_REF, nargs='?', type=str,
            default=NEWEST_VERSION,
            help=arg_help.PACKAGE_LOAD)
        arg(OPTIONAL_INPUT_NICK)
        arg(OPTIONAL_WORKSPACE)

    def run(self, args):
        input_nick = args.input_nick
        package_ref = args.package_ref
        workspace = args.workspace
        kwargs = dict(args.query or {})
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


class CmdLoad(Command):
    '''
    Put defined input data in place.
    '''

    def arguments(self, arg):
        arg(OPTIONAL_INPUT_NICK)
        arg(OPTIONAL_WORKSPACE)

    def run(self, args):
        input_nick = args.input_nick
        workspace = args.workspace
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
