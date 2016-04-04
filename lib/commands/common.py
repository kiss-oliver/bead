from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from argh.decorators import arg
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


def opt_workspace(func):
    '''
    Define `workspace` as option, defaulting to current directory
    '''
    decorate = arg(
        '--workspace', '-w', metavar=arg_metavar.WORKSPACE,
        type=Workspace, default=CurrentDirWorkspace(),
        help=arg_help.WORKSPACE)
    return decorate(func)


class DefaultArgSentinel(object):
    '''
    I am a sentinel for @argh.arg default values.

    I.e. If you see me, it means that you got the default value.

    I also provide sensible description for the default value.
    '''

    def __init__(self, description):
        self.description = description

    def __repr__(self):
        return self.description


def package_spec_kwargs(func):
    # TODO: implement more options
    for modifier in [
        # -r, --repo, --repository

        # package_filters
        arg('-o', '--older', '--older-than', dest='older_than',
            metavar='TIMEDELTA'),
        arg('-n', '--newer', '--newer-than', dest='newer_than',
            metavar='TIMEDELTA'),
        # arg('-d', '--date', dest='date'),

        # match reducers
        # -N, --next
        # -P, --prev, --previous
        # --newest, --latest (default)
        # --oldest
    ]:
        func = modifier(func)
    return func


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
        # FIXME: ArchiveReference.default_workspace: also remove trailing extension, and '[-_.0-9]'' characters
        return Workspace(repos.package_name_from_file_path(self.package_path))


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

    from argh import ArghParser, named

    @named('get')
    @package_spec_kwargs
    def cmd(other, **kwargs):
        spec = parse_package_spec_kwargs(kwargs)
        print(spec.package_filters)
        print(other, kwargs)

    p = ArghParser()
    # p.set_default_command(cmd)
    p.add_commands([cmd])
    p.dispatch()
