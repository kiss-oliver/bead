from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import sys

import appdirs
from .cmdparse import Parser, Command

from . import workspace
from . import input
from . import repo

PACKAGE = __name__
VERSION = '0.0.1'


def initialize_env(config_dir):
    import bead.repos
    bead.repos.initialize(config_dir)


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
            workspace.CmdNew,
            'Create and initialize new workspace directory with a new bead.',

            'develop',
            workspace.CmdDevelop,
            'Create workspace from specified bead.',

            'save',
            workspace.CmdSave,
            'Save workspace in a repository.',

            'status',
            workspace.CmdStatus,
            'Show workspace information.',

            'nuke',
            workspace.CmdNuke,
            'Delete workspace.',

            'version',
            CmdVersion,
            'Show program version.'))

    (parser
        .group('input', 'Manage data loaded from other beads')
        .commands(
            # named('unload')(unload_input),
            'add',
            input.CmdAdd,
            'Define dependency and load its data.',

            'delete',
            input.CmdDelete,
            'Forget all about an input.',

            'update',
            input.CmdUpdate,
            'Update input[s] to newest version or defined bead.',

            'load',
            input.CmdLoad,
            'Load data from already defined dependency.',))

    (parser
        .group('repo', 'Manage bead repositories')
        .commands(
            'add',
            repo.CmdAdd,
            'Define a repository.',

            'list',
            repo.CmdList,
            'Show known repositories.',

            'forget',
            repo.CmdForget,
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
