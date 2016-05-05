from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import appdirs
import sys

from .commands.cmdparse import Parser, Command
from . import commands
from . import PACKAGE, VERSION


def initialize_env(config_dir):
    from . import repos
    repos.initialize(config_dir)


class CmdVersion(Command):
    '''
    Show program version
    '''

    def run(self, args):
        print('{} version {}'.format(PACKAGE, VERSION))


def make_argument_parser():
    parser = Parser.new(prog=__name__)
    (parser
        .commands(
            'new',
            commands.workspace.CmdNew,
            'Create and initialize new workspace directory with a new package.',

            'develop',
            commands.workspace.CmdDevelop,
            'Create workspace from specified package.',

            'save',
            commands.workspace.CmdSave,
            'Save workspace in a repository.',

            'status',
            commands.workspace.CmdStatus,
            'Show workspace information.',

            'nuke',
            commands.workspace.CmdNuke,
            'Delete workspace.',

            'version',
            CmdVersion,
            'Show program version.'))
    (parser
        .group('input', 'Manage data loaded from other packages')
        .commands(
            # named('unload')(unload_input),
            'add',
            commands.input.CmdAdd,
            'Define dependency and load its data.',

            'delete',
            commands.input.CmdDelete,
            'Forget all about an input.',

            'update',
            commands.input.CmdUpdate,
            'Update input[s] to newest version or defined package.',

            'load',
            commands.input.CmdLoad,
            'Load data from already defined dependency.',))

    (parser
        .group('repo', 'Manage package repositories')
        .commands(
            'add',
            commands.repo.CmdAdd,
            'Define a repository.',

            'list',
            commands.repo.CmdList,
            'Show known repositories.',

            'forget',
            commands.repo.CmdForget,
            'Forget a known repository.'))

    return parser


def run(argv):
    parser = make_argument_parser()
    return parser.dispatch(argv)


def main():
    config_dir = appdirs.user_config_dir(
        PACKAGE + '-6a4d9d98-8e64-4a2a-b6c2-8a753ea61daf')
    initialize_env(config_dir)
    try:
        retval = run(sys.argv[1:])
    except BaseException as e:
        retval = e
    sys.exit(retval)


if __name__ == '__main__':
    main()
