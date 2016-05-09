from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import sys

from ..pkg.workspace import Workspace, CurrentDirWorkspace
from ..pkg import spec as pkg_spec
from ..pkg.archive import Archive
from .. import repos
from . import arg_help
from . import arg_metavar
from ..tech.timestamp import time_from_user

ERROR_EXIT = 1


def die(msg):
    sys.stderr.write('ERROR: ')
    sys.stderr.write(msg)
    sys.stderr.write('\n')
    sys.exit(ERROR_EXIT)


def warning(msg):
    sys.stderr.write('WARNING: ')
    sys.stderr.write(msg)
    sys.stderr.write('\n')


def OPTIONAL_WORKSPACE(parser):
    '''
    Define `workspace` as option, defaulting to current directory
    '''
    parser.arg(
        '--workspace', '-w', metavar=arg_metavar.WORKSPACE,
        type=Workspace, default=CurrentDirWorkspace(),
        help=arg_help.WORKSPACE)


class DefaultArgSentinel(object):
    '''
    I am a sentinel for default values.

    I.e. If you see me, it means that you got the default value.

    I also provide human sensible description for the default value.
    '''

    def __init__(self, description):
        self.description = description

    def __repr__(self):
        return self.description


def tag(tag, parse):
    '''
    Make a function that parses and tags its input

    parse is a function with one parameter,
    it is expected to raise a ValueError if there is any problem
    '''
    return lambda value: (tag, parse(value))


def _parse_time(timeish):
    return time_from_user(timeish)


def _parse_start_of_name(name):
    return name + '*'


def package_spec_kwargs(parser):
    group = parser.argparser.add_argument_group(
        'package query',
        'Restrict the package version with these options')
    arg = group.add_argument
    # TODO: implement more options
    # -r, --repo, --repository

    # package_filters
    BEAD_QUERY = 'package_query'
    arg('-o', '--older', '--older-than', dest=BEAD_QUERY,
        metavar='TIMEDEF', type=tag(pkg_spec.OLDER_THAN, _parse_time))
    arg('-n', '--newer', '--newer-than', dest=BEAD_QUERY,
        metavar='TIMEDEF', type=tag(pkg_spec.NEWER_THAN, _parse_time))
    arg('--start-of-name', dest=BEAD_QUERY,
        metavar='START-OF-BEAD-NAME',
        type=tag(pkg_spec.BEAD_NAME_GLOB, _parse_start_of_name))

    # match reducers
    # -N, --next
    # -P, --prev, --previous
    # --newest, --latest (default)
    # --oldest


class PackageReference:
    package = Archive
    default_workspace = Workspace


class ArchiveReference(PackageReference):
    def __init__(self, package_path):
        self.package_path = package_path

    @property
    def package(self):
        if os.path.isfile(self.package_path):
            return Archive(self.package_path)
        raise LookupError('Not a file', self.package_path)

    @property
    def default_workspace(self):
        return Workspace(self.package.name)


class RepoQueryReference(PackageReference):
    def __init__(self, workspace_name, query, repositories, index=-1):
        # index: like python list indices 0 = first, -1 = last
        self.workspace_name = workspace_name
        self.query = query
        if index < 0:
            self.order = pkg_spec.NEWEST_FIRST
            self.limit = -index
        else:
            self.order = pkg_spec.OLDEST_FIRST
            self.limit = index + 1
        self.repositories = list(repositories)

    @property
    def package(self):
        matches = []
        for repo in self.repositories:
            matches.extend(repo.find_packages(self.query, self.order, self.limit))
            # XXX order_and_limit_packages is called twice - first in find_packages
            matches = repos.order_and_limit_packages(matches, self.order, self.limit)
        if len(matches) == self.limit:
            return matches[-1]
        raise LookupError

    @property
    def default_workspace(self):
        return Workspace(self.workspace_name)


def get_package_ref(package_name, package_query):
    if os.path.sep in package_name and os.path.isfile(package_name):
        return ArchiveReference(package_name)

    query = list(package_query or [])

    if package_name:
        query = [(pkg_spec.BEAD_NAME_GLOB, package_name)] + query

    # TODO: calculate and add index parameter (--next, --prev)
    return RepoQueryReference(package_name, query, repos.env.get_repos())
