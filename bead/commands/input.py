from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from .cmdparse import Command

from ..commands import arg_metavar
from ..commands import arg_help
from ..commands.common import (
    OPTIONAL_WORKSPACE, DefaultArgSentinel,
    CurrentDirWorkspace,
    die, warning
)
from ..commands.common import bead_spec_kwargs, get_bead_ref, RepoQueryReference
from ..pkg import spec as bead_spec
from .. import repos
from ..tech.timestamp import time_from_timestamp


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


# bead_ref
NEWEST_VERSION = DefaultArgSentinel('same bead, newest version')
USE_INPUT_NICK = DefaultArgSentinel('use {}'.format(arg_metavar.INPUT_NICK))
# default workspace
CURRENT_DIRECTORY = CurrentDirWorkspace()


class CmdAdd(Command):
    '''
    Make data from another bead available in the input directory.
    '''

    def declare(self, arg):
        arg(MANDATORY_INPUT_NICK)
        arg('bead_name', metavar=arg_metavar.BEAD_REF, nargs='?', type=str,
            default=USE_INPUT_NICK,
            help=arg_help.BEAD_LOAD)
        arg(bead_spec_kwargs)
        arg(OPTIONAL_WORKSPACE)

    def run(self, args):
        input_nick = args.input_nick
        bead_name = args.bead_name
        workspace = args.workspace

        if bead_name is USE_INPUT_NICK:
            bead_name = input_nick

        bead_ref = get_bead_ref(bead_name, args.bead_query)
        try:
            bead = bead_ref.bead
        except LookupError:
            die('Not a known bead name: {}'.format(bead_name))

        _check_load_with_feedback(
            workspace, args.input_nick, bead, bead_name)


class CmdDelete(Command):
    '''
    Forget all about an input.
    '''

    def declare(self, arg):
        arg(MANDATORY_INPUT_NICK)
        arg(OPTIONAL_WORKSPACE)

    def run(self, args):
        input_nick = args.input_nick
        workspace = args.workspace
        workspace.delete_input(input_nick)
        print('Input {} is deleted.'.format(input_nick))


class CmdUpdate(Command):
    '''
    Update input[s] to newest version or defined bead.
    '''

    def declare(self, arg):
        arg(bead_spec_kwargs)
        arg(OPTIONAL_INPUT_NICK)
        arg(
            'bead_ref', metavar=arg_metavar.BEAD_REF, nargs='?', type=str,
            default=NEWEST_VERSION,
            help=arg_help.BEAD_LOAD)
        arg(OPTIONAL_WORKSPACE)

    def run(self, args):
        input_nick = args.input_nick
        bead_ref = args.bead_ref
        workspace = args.workspace
        if input_nick is ALL_INPUTS:
            for input in workspace.inputs:
                try:
                    _update(workspace, input)
                except LookupError:
                    if workspace.is_loaded(input.name):
                        print('{} is already newest ({})'.format(input.name, input.timestamp))
                    else:
                        warning('Can not find bead for {}'.format(input.name))
            print('All inputs are up to date.')
        else:
            # FIXME: update: fix to allow to select previous/next/closest to a timestamp bead
            if bead_ref is not NEWEST_VERSION:
                bead_ref = get_bead_ref(bead_ref, args.bead_query)
            try:
                _update(workspace, workspace.get_input(input_nick), bead_ref)
            except LookupError:
                die('Can not find matching bead')


def _update(workspace, input, bead_ref=NEWEST_VERSION):
    if bead_ref is NEWEST_VERSION:
        # FIXME: input._update
        query = [
            (bead_spec.BEAD_UUID, input.bead_uuid),
            (bead_spec.NEWER_THAN, time_from_timestamp(input.timestamp))]
        workspace_name = ''  # no workspace!
        bead_ref = RepoQueryReference(workspace_name, query, repos.env.get_repos())

    replacement = bead_ref.bead
    _check_load_with_feedback(workspace, input.name, replacement)


class CmdLoad(Command):
    '''
    Put defined input data in place.
    '''

    def declare(self, arg):
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
            bead = repos.get_bead(input.bead_uuid, input.content_hash)
        except LookupError:
            warning(
                'Could not find archive for {} - not loaded!'
                .format(input.name))
        else:
            _check_load_with_feedback(workspace, input.name, bead)
    else:
        print('Skipping {} (already loaded)'.format(input.name))


def _check_load_with_feedback(
        workspace, input_name, bead, bead_name=None):
    if bead.is_valid:
        if workspace.is_loaded(input_name):
            workspace.unload(input_name)
        workspace.load(input_name, bead)
        if bead_name:
            print('{} loaded on {}.'.format(bead_name, input_name))
        else:
            print('Loaded {}.'.format(input_name))
    else:
        warning(
            'Bead for {} is found but damaged - not loading.'
            .format(input_name))
