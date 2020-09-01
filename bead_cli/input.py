import os.path

from .cmdparse import Command

from . import arg_metavar
from . import arg_help
from .common import (
    OPTIONAL_WORKSPACE, OPTIONAL_ENV,
    DefaultArgSentinel, assert_valid_workspace,
    verify_with_feedback,
    die, warning
)
from .common import BEAD_REF_BASE_defaulting_to, BEAD_OFFSET, BEAD_TIME, resolve_bead, TIME_LATEST
from bead.box import UnionBox
from bead.workspace import Workspace
import bead.spec as bead_spec

# input_nick
ALL_INPUTS = DefaultArgSentinel('all inputs')


def OPTIONAL_INPUT_NICK(parser):
    '''
    Declare `input_nick` as optional parameter
    '''
    parser.arg(
        'input_nick', type=type(''), nargs='?', default=ALL_INPUTS,
        metavar=arg_metavar.INPUT_NICK, help=arg_help.INPUT_NICK)


def INPUT_NICK(parser):
    '''
    Declare `input_nick` as mandatory parameter
    '''
    parser.arg(
        'input_nick',
        metavar=arg_metavar.INPUT_NICK, help=arg_help.INPUT_NICK)


# bead_ref
SAME_BEAD_NEWEST_VERSION = DefaultArgSentinel('same bead, newest version')
USE_INPUT_NICK = DefaultArgSentinel(f'use {arg_metavar.INPUT_NICK}')


class CmdAdd(Command):
    '''
    Make data from another bead available in the input directory.
    '''

    def declare(self, arg):
        arg(INPUT_NICK)
        arg(BEAD_REF_BASE_defaulting_to(USE_INPUT_NICK))
        arg(BEAD_TIME)
        arg(OPTIONAL_WORKSPACE)
        arg(OPTIONAL_ENV)

    def run(self, args):
        input_nick = args.input_nick
        bead_ref_base = args.bead_ref_base
        workspace = get_workspace(args)
        env = args.get_env()

        if os.path.dirname(input_nick):
            die(f'Invalid input name: {input_nick}')

        if bead_ref_base is USE_INPUT_NICK:
            bead_ref_base = input_nick

        try:
            bead = resolve_bead(env, bead_ref_base, args.bead_time)
        except LookupError:
            die(f'Not a known bead name: {bead_ref_base}')

        _check_load_with_feedback(workspace, args.input_nick, bead)


class CmdDelete(Command):
    '''
    Forget all about an input.
    '''

    def declare(self, arg):
        arg(INPUT_NICK)
        arg(OPTIONAL_WORKSPACE)

    def run(self, args):
        input_nick = args.input_nick
        workspace = get_workspace(args)
        workspace.delete_input(input_nick)
        print(f'Input {input_nick} is deleted.')


class CmdUpdate(Command):
    '''
    Update input[s] to newest version or defined bead.
    '''

    def declare(self, arg):
        arg(OPTIONAL_INPUT_NICK)
        arg(BEAD_REF_BASE_defaulting_to(SAME_BEAD_NEWEST_VERSION))
        arg(BEAD_TIME)
        arg(BEAD_OFFSET)
        arg(OPTIONAL_WORKSPACE)
        arg(OPTIONAL_ENV)

    def run(self, args):
        if args.input_nick is ALL_INPUTS:
            self.update_all_inputs(args)
        else:
            self.update_one_input(args)

    def update_all_inputs(self, args):
        assert args.bead_ref_base is SAME_BEAD_NEWEST_VERSION
        assert not args.bead_offset, "--next, --prev can not be specified when updating all inputs"
        workspace = get_workspace(args)
        env = args.get_env()
        unionbox = UnionBox(env.get_boxes())
        for input in workspace.inputs:
            bead_name = workspace.get_input_bead_name(input.name)
            try:
                bead = unionbox.get_at(
                    check_type=bead_spec.BEAD_NAME,
                    check_param=bead_name,
                    time=args.bead_time)
            except LookupError:
                if workspace.is_loaded(input.name):
                    print(
                        f'Skipping update of "{input.name}":'
                        + f' no other candidate found ({bead_name}@{input.timestamp})')
                else:
                    warning(f'Could not find bead for "{input.name}" with name "{bead_name}"')
            else:
                _update_input(workspace, input, bead)
        print('All inputs are up to date.')

    def update_one_input(self, args):
        input_nick = args.input_nick
        bead_ref_base = args.bead_ref_base
        workspace = get_workspace(args)
        env = args.get_env()
        input = workspace.get_input(input_nick)
        if bead_ref_base is SAME_BEAD_NEWEST_VERSION:
            def get_context(time):
                unionbox = UnionBox(env.get_boxes())
                bead_name = workspace.get_input_bead_name(input.name)
                try:
                    return unionbox.get_context(
                        check_type=bead_spec.BEAD_NAME,
                        check_param=bead_name,
                        time=time)
                except LookupError:
                    die(f'Could not find bead for "{input.name}" with name "{bead_name}"')

            if args.bead_offset:
                # handle --prev --next
                assert args.bead_time == TIME_LATEST
                context = get_context(input.timestamp)
                if args.bead_offset == 1:
                    bead = context.next
                else:
                    bead = context.prev
            else:
                # --time
                bead = get_context(args.bead_time).best
        else:
            # path or new bead by name - same as input add, develop
            assert args.bead_offset == 0
            bead = resolve_bead(env, bead_ref_base, args.bead_time)
        if bead:
            _update_input(workspace, input, bead)
        else:
            die('Can not find matching bead')


def _update_input(workspace, input, bead):
    if workspace.is_loaded(input.name) and input.content_id == bead.content_id:
        assert input.kind == bead.kind
        assert input.timestamp == bead.timestamp
        print(
            f'Skipping update of {input.name}:'
            + f' it is already at requested version ({input.timestamp})')
    else:
        if input.kind != bead.kind:
            warning(f'Updating input "{input.name}" with a bead of different kind')
        _check_load_with_feedback(workspace, input.name, bead)


class CmdLoad(Command):
    '''
    Put defined input data in place.
    '''

    def declare(self, arg):
        arg(OPTIONAL_INPUT_NICK)
        arg(OPTIONAL_WORKSPACE)
        arg(OPTIONAL_ENV)

    def run(self, args):
        input_nick = args.input_nick
        workspace = get_workspace(args)
        env = args.get_env()
        if input_nick is ALL_INPUTS:
            inputs = workspace.inputs
            if inputs:
                for input in inputs:
                    _load(env, workspace, input)
            else:
                warning('No inputs defined to load.')
        else:
            if not workspace.has_input(input_nick):
                die(f'No input with name {input_nick}')
            _load(env, workspace, workspace.get_input(input_nick))


def _load(env, workspace, input):
    assert input is not None
    if not workspace.is_loaded(input.name):
        name = workspace.get_input_bead_name(input.name)
        content_id = input.content_id
        bead = None
        for box in env.get_boxes():
            bead = box.find_bead(name, content_id)
            if bead:
                break
        if bead is None:
            warning(f'Could not find archive named {name} for input {input.name} - not loaded!')
            return
        _check_load_with_feedback(workspace, input.name, bead)
    else:
        print(f'Skipping {input.name} (already loaded)')


def _check_load_with_feedback(workspace, input_nick, bead):
    is_valid = verify_with_feedback(bead)
    if is_valid:
        workspace.set_input_bead_name(input_nick, bead.name)
        if workspace.is_loaded(input_nick):
            print(f'Removing current data from {input_nick}')
            workspace.unload(input_nick)
        print(f'Loading new data to {input_nick} ...', end='', flush=True)
        workspace.load(input_nick, bead)
        print(' Done')
    else:
        warning(f'Bead for {input_nick} is found but damaged - not loading.')


class CmdUnload(Command):
    '''
    Remove input data.
    '''

    def declare(self, arg):
        arg(OPTIONAL_INPUT_NICK)
        arg(OPTIONAL_WORKSPACE)

    def run(self, args):
        input_nick = args.input_nick
        workspace = get_workspace(args)
        if input_nick is ALL_INPUTS:
            for input in workspace.inputs:
                _unload(workspace, input.name)
        else:
            _unload(workspace, input_nick)


def _unload(workspace, input_nick):
    if workspace.is_loaded(input_nick):
        print('Unloading', input_nick, '...', end='', flush=True)
        workspace.unload(input_nick)
        print(' Done', flush=True)
    else:
        print(input_nick, 'was not loaded - skipping')


def get_workspace(args) -> Workspace:
    assert_valid_workspace(args.workspace)
    return args.workspace
