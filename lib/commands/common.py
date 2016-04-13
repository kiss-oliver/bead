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


def tag(tag):
    '''
    Make a function that tags its input
    '''
    return lambda value: (tag, value)


def package_spec_kwargs(parser):
    group = parser.argparser.add_argument_group(
        'package query',
        'Restrict the package version with these options')
    arg = group.add_argument
    # TODO: implement more options
    # -r, --repo, --repository

    # package_filters
    arg('-o', '--older', '--older-than', dest='query',
        metavar='TIMEDELTA', type=tag('older_than'))
    arg('-n', '--newer', '--newer-than', dest='query',
        metavar='TIMEDELTA', type=tag('newer_than'))
    # arg('-d', '--date', dest='date'),

    # match reducers
    # -N, --next
    # -P, --prev, --previous
    # --newest, --latest (default)
    # --oldest


def parse_package_spec_kwargs(kwargs):
    # assert False, kwargs
    query = pkg_spec.PackageQuery()
    query_modifier = {
        'older_than': query.is_older_than,
        'newer_than': query.is_newer_than,
    }
    for attr in kwargs:
        if kwargs[attr] is not None:
            query = query_modifier[attr](kwargs[attr])
    # FIXME: parse_package_spec_kwargs: determine reducers
    return query


class PackageReference:
    package = Archive
    default_workspace = str


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
    def __init__(self, package_name, query, repositories):
        self.package_name = package_name
        self.query = query
        self.repositories = repositories

    @property
    def package(self):
        try:
            package = next(self.query.get_packages(self.repositories))
        except StopIteration:
            raise LookupError
        return package

    @property
    def default_workspace(self):
        return Workspace(self.package_name)


def get_package_ref(package_name, kwargs):
    if os.path.sep in package_name and os.path.isfile(package_name):
        return ArchiveReference(package_name)
    # assert False, 'FIXME: get_package_ref - repo search'
    query = parse_package_spec_kwargs(kwargs)
    query.by_name(package_name)
    return RepoQueryReference(package_name, query, repos.env.get_repos())


# ----------------------------------------------------------------------------------
# TODO: delete experimental code

if __name__ == '__main__':
    # parse time-delta
    # TODO: make
    import re
    re.match(r'(([+-]?\d+) *([ymwdHMS]))*$', '2w12H  13M')
    re.findall(r'([+-]?\d+) *([ymwdHMS])', 'asd +-12H +13M x')
