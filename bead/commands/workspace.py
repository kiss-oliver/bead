from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os

from .. import tech
from ..pkg.workspace import Workspace, CurrentDirWorkspace
from ..pkg import layouts

from .cmdparse import Command
from .common import die, warning
from .common import DefaultArgSentinel
from .common import OPTIONAL_WORKSPACE
from .common import package_spec_kwargs, get_package_ref
from . import arg_metavar
from . import arg_help
from .. import repos


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


class CmdNew(Command):
    '''
    Create and initialize new workspace directory with a new package.
    '''

    def declare(self, arg):
        arg('workspace', type=Workspace, metavar=arg_metavar.WORKSPACE,
            help='package and directory to create')

    def run(self, args):
        workspace = args.workspace
        assert_may_be_valid_name(workspace.package_name)
        # FIXME: die with message when directory already exists

        uuid = tech.identifier.uuid()
        workspace.create(uuid)
        print('Created {}'.format(workspace.package_name))


CURRENT_DIRECTORY = CurrentDirWorkspace()


def workspace_defaulting_to(default_workspace):
    def opt_workspace(parser):
        parser.arg(
            'workspace', nargs='?', type=Workspace,
            default=default_workspace,
            metavar=arg_metavar.WORKSPACE, help=arg_help.WORKSPACE)
    return opt_workspace


USE_THE_ONLY_REPO = DefaultArgSentinel(
    'if there is exactly one repository,' +
    ' store there, otherwise it MUST be specified')


class CmdSave(Command):
    '''
    Save workspace in a repository.
    '''

    def declare(self, arg):
        arg('repo_name', nargs='?', default=USE_THE_ONLY_REPO, type=str,
            metavar='REPOSITORY', help='Name of repository to store package')
        arg(OPTIONAL_WORKSPACE)

    def run(self, args):
        repo_name = args.repo_name
        workspace = args.workspace
        assert_valid_workspace(workspace)
        if repo_name is USE_THE_ONLY_REPO:
            repositories = list(repos.env.get_repos())
            if not repositories:
                die('No repositories defined, please define one!')
            if len(repositories) > 1:
                die(
                    'REPOSITORY parameter is not optional!\n' +
                    '(more than one repositories exists)')
            repo = repositories[0]
        else:
            repo = repos.get(repo_name)
            if repo is None:
                die('Unknown repository: {}'.format(repo_name))
        repo.store(workspace, timestamp())
        print('Successfully stored package.')


DERIVE_FROM_PACKAGE_NAME = DefaultArgSentinel('derive one from package name')


class CmdDevelop(Command):
    '''
    Unpack a package as a source tree.

    Package directory layout is created, but only the source files are
    extracted by default.
    '''

    def declare(self, arg):
        arg('package_name', metavar='package-name')
        arg(package_spec_kwargs)
        # TODO: delete arg_metavar.PACKAGE_REF, arg_help.PACKAGE_REF
        arg(workspace_defaulting_to(DERIVE_FROM_PACKAGE_NAME))
        arg('-x', '--extract-output', dest='extract_output',
            default=False, action='store_true',
            help='Extract output data as well (normally it is not needed!).')

    def run(self, args):
        extract_output = args.extract_output
        package_ref = get_package_ref(args.package_name, args.package_query)
        try:
            package = package_ref.package
        except LookupError:
            die('Package not found!')
        if not package.is_valid:
            die('Package is found but damaged')
        if args.workspace is DERIVE_FROM_PACKAGE_NAME:
            workspace = package_ref.default_workspace
        else:
            workspace = args.workspace

        package.unpack_to(workspace)
        assert workspace.is_valid

        if extract_output:
            output_directory = workspace.directory / layouts.Workspace.OUTPUT
            package.unpack_data_to(output_directory)

        print('Extracted source into {}'.format(workspace.directory))
        # XXX: try to load smaller inputs?
        if workspace.inputs:
            print('Input data not loaded, update if needed and load manually')


def assert_valid_workspace(workspace):
    if not workspace.is_valid:
        die('{} is not a valid workspace'.format(workspace.directory))


def indent(lines):
    return ('\t' + line for line in lines)


def _status_version_timestamp(input):
    return (
        'Release time',
        repos.get_package(input.package, input.version).timestamp_str)


def get_package_name(package_uuid):
    # FIXME workspace.get_package_name
    raise LookupError(package_uuid)


def _status_package_name(input):
    return ('Package name', get_package_name(input.package))


def _status_package_uuid(input):
    return ('Package UUID', input.package)


def _status_version_hash(input):
    return ('Version hash', input.version)


def first(*fields):
    '''
    First available field
    '''
    def field(input):
        for field in fields:
            try:
                return field(input)
            except LookupError:
                pass
        raise LookupError()
    return field


ALL_FIELDS = (
    _status_package_name,
    _status_package_uuid,
    _status_version_timestamp,
    _status_version_hash,
)


DEFAULT_FIELDS = (
    first(_status_package_name, _status_package_uuid),
    first(_status_version_timestamp, _status_version_hash),
)


def format_input(input, fields):
    yield '- {0} (input/{0})'.format(input.name)
    for field in fields:
        try:
            name, value = field(input)
        except LookupError:
            pass
        else:
            yield '\t{}: {}'.format(name, value)


def print_inputs(workspace, fields=ALL_FIELDS):
    assert_valid_workspace(workspace)
    inputs = sorted(workspace.inputs)

    if inputs:
        print('Inputs:')

        input_separator = ''
        for input in inputs:
            print(input_separator, end='')
            print(
                '\n'.join(indent(format_input(input, fields)))
                .expandtabs(2))
            input_separator = os.linesep

        print('')
        unloaded = [
            input.name
            for input in inputs
            if not workspace.is_loaded(input.name)]
        if unloaded:
            print('These inputs are not loaded:')
            unloaded_list = '\t- ' + '\n\t- '.join(unloaded)
            print(unloaded_list.expandtabs(2))
            print('You can "load" or "update" them manually.')


class CmdStatus(Command):
    '''
    Show workspace status - name of package, inputs and their unpack status.
    '''

    def declare(self, arg):
        arg(OPTIONAL_WORKSPACE)
        arg('-v', '--verbose', default=False, action='store_true',
            help='show more detailed information')

    def run(self, args):
        workspace = args.workspace
        verbose = args.verbose
        # TODO: use a template and render it with passing in all data
        uuid_needed = verbose
        if workspace.is_valid:
            print('Package Name: {}'.format(workspace.package_name))
            if uuid_needed:
                print('Package UUID: {}'.format(workspace.uuid))
            print()
            print_inputs(
                workspace, DEFAULT_FIELDS if not verbose else ALL_FIELDS)
        else:
            warning('Invalid workspace ({})'.format(workspace.directory))


class CmdNuke(Command):
    '''
    Delete the workspace, inluding data, code and documentation.
    '''

    def declare(self, arg):
        arg(workspace_defaulting_to(CURRENT_DIRECTORY))

    def run(self, args):
        workspace = args.workspace
        assert_valid_workspace(workspace)
        directory = workspace.directory
        tech.fs.rmtree(directory)
        print('Deleted workspace {}'.format(directory))
