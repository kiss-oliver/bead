# TODO: names/translations management commands
# - export [--peer name] filename
# - import peer filename
# - rename-peer old-name new-name
# - delete-peer name
# - rename-package old-name new-name
# - delete-package package-name
# - lift peer:name [local-name]


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import appdirs
import os
import sys

from argh import ArghParser
from . import commands
from . import PACKAGE, VERSION


def initialize_env(config_dir):
    try:
        os.makedirs(config_dir)
    except OSError:
        assert os.path.isdir(config_dir)


def make_argument_parser():
    parser = ArghParser(prog=__name__)
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_commands(
        [
            commands.workspace.new,
            commands.workspace.develop,
            commands.workspace.save,
            commands.workspace.status,
            commands.workspace.nuke,
            # TODO: #10 names for packages
            # rename  # package
        ])
    # FIXME: ArghParser.add_subcommands
    # https://github.com/neithere/argh/issues/88
    parser.add_commands(
        [
            commands.input.load,
            # named('unload')(unload_input),
            commands.input.add,
            commands.input.delete,
            commands.input.update,
        ],
        namespace='input',
        namespace_kwargs=dict(
            title='Manage data loaded from other packages...',
        ))
    parser.add_commands(
        [
            commands.repo.add,
            commands.repo.list,
            commands.repo.forget,
        ],
        namespace='repo',
        namespace_kwargs=dict(
            title='Manage package repositories...',
        ))
    parser.add_commands(
        [
            commands.dict.add,
            commands.dict.merge,
            # commands.dict.copy,
            commands.dict.rename,
            commands.dict.forget,
            # commands.dict.list,
            commands.dict.export,
            commands.dict.import_,
        ],
        namespace='dict',
        namespace_kwargs=dict(
            title='Manage package names...',
        ))
    return parser


def run(argv):
    parser = make_argument_parser()
    parser.dispatch(argv)
    # TODO verify exit status


def main():
    config_dir = appdirs.user_config_dir(
        PACKAGE + '-6a4d9d98-8e64-4a2a-b6c2-8a753ea61daf')
    initialize_env(config_dir)
    run(sys.argv[1:])


if __name__ == '__main__':
    main()
