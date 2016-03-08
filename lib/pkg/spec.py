from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import re
from collections import namedtuple


# TODO: parse and return 'offset' - "offset to last matching version"
PackageSpec = namedtuple('PackageSpec', 'repo name version offset')
ALL_REPOSITORIES = object()


'''
-r, --repo, --repository


package_filters
-o, --older, --older-than
-n, --newer, --newer-than
-d, --date
-N, --next
-P, --prev, --previous
--timedelta

match reducers
--newest (default)
-O, --oldest
'''

_parse = re.compile(
    r'''
    ^
    # repo is optional
    (
        (?P<repo>[^:@]*)
        :
    )?

    # name is mandatory
    (?P<name>[^:@]+)

    # version is optional
    (
        @
        (?P<version>[^-:@]+)?
        (-(?P<offset>[0-9]+))?
    )?
    $
    ''', re.VERBOSE).match


def parse(string):
    '''
    Parse a string based package specification.

    Parts of the returned package specification:
    - repo (optional, defaults to all repositories)
    - name (mandatory)
    - version (optional, defaults to None)
    '''
    match = _parse(string)
    if match:
        m = match.groupdict()
        return PackageSpec(
            m['repo'] or ALL_REPOSITORIES,
            m['name'],
            m['version'],
            int(m['offset'] or '0'))
    raise ValueError('Not a valid package specification', string)


class PackageQuery:

    def __init__(self, repositories, spec, first_matches=False):
        self.repositories = repositories
        self.spec = spec
        self.first_matches = first_matches

    def get_packages(self):
        packages = []
        for repo in self.repositories:
            for package in self.query_repo(repo):
                if self.matching_package(package):
                    packages.append(package)
                    packages = self.fold_packages(packages)
                    if self.first_matches and packages:
                        return packages
        return packages


class PackageSpec:

    def __init__(self):
        self.repo_queries = []
        self.package_filters = []
        self.match_reducers = []

    def query_repo(self, repo):
        '''
            Retrieve match candidates from a repository
        '''
        for query in self.repo_queries:
            for package in query(repo):
                yield package

    def matching_package(self, package):
        '''
            Decide if a package matches or not
        '''
        for pass_filter in self.package_filters:
            if not pass_filter(package):
                return False
        return True

    def fold_packages(self, packages):
        '''
            Drop suboptimal packages

            e.g. keep only the latest, or the closest one
        '''
        for match_reducer in self.match_reducers:
            packages = match_reducer(packages)
        return packages

    # Construct
    def add_repo_query(self, pkg_query):
        '''
            Use :pkg_query: for querying repos for package candidates.
        '''
        self.repo_queries.append(pkg_query)

    def add_package_filter(self, pkg_filter):
        '''
            Restrict packages to those matching :pkg_filter:
        '''
        self.package_filters.append(pkg_filter)

    def add_match_reducer(self, match_reducer):
        '''
            Reduce matches - keep only the best one[s]
        '''
        self.match_reducers.append(match_reducer)


# repo queries
def query_by_name(package_name):
    def query(repo):
        return repo.all_by_name(name)
    return query


def query_by_uuid(package_uuid, content_hash=None):
    def query(repo):
        return repo.all_by_uuid(package_uuid, content_hash)
    return query


# package filters
def newer_than(timestamp):
    def filter(pkg):
        return pkg.timestamp > timestamp
    return filter


def older_than(timestamp):
    def filter(pkg):
        return pkg.timestamp < timestamp
    return filter


def content_prefix(hash_prefix):
    def filter(pkg):
        return pkg.version.startswith(hash_prefix)
    return filter


def timestamp_prefix(timestamp_str):
    def filter(pkg):
        return pkg.timestamp_str.startswith(timestamp_str)
    return filter


# match reducers
def newest(packages):
    return sorted(packages, key=lambda pkg: pkg.timestamp, reverse=True)[:1]


def oldest(packages):
    return sorted(packages, key=lambda pkg: pkg.timestamp)[:1]





# FIXME: find proper place for spec.package_spec_kwargs, parse_package_spec_kwargs

from argh import ArghParser, arg, named

def package_spec_kwargs(func):
    for modifier in [
        arg('-o', '--older', '--older-than', dest='older_than'),
        arg('-n', '--newer', '--newer-than', dest='newer_than'),
        arg('-d', '--date', dest='date'),
    ]:
        func = modifier(func)
    return func


def parse_package_spec_kwargs(kwargs):
    arg_to_filter = {
        'older_than': older_than,
        'newer_than': newer_than,
        'date': timestamp_prefix,
    }
    spec = PackageSpec()
    for attr in arg_to_filter:
        spec.add_package_filter(arg_to_filter[attr](kwargs[attr]))
    return spec


if __name__ == '__main__':
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
