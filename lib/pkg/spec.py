from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import functools


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


class PackageQuery:

    def __init__(self):
        self.repo_queries = []
        self.package_filters = []
        self.match_reducers = []

    def get_packages(self, repositories):
        '''
            Generate matching packages
        '''
        packages = (
            package
            for repo in self.repositories
            for package in self.query_repo(repo)
            if self.matching_package(package))
        return self.fold_packages(packages)

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
        return repo.all_by_name(package_name)
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
    newer_pkg = functools.partial(max, key=lambda pkg: pkg.timestamp)
    try:
        # squeze the first item, so empty candidate list can be recognized & handled
        yield functools.reduce(newer_pkg, packages, next(packages))
    except StopIteration:
        return
    # return sorted(packages, key=lambda pkg: pkg.timestamp, reverse=True)[:1]


def oldest(packages):
    older_pkg = functools.partial(min, key=lambda pkg: pkg.timestamp)
    try:
        # squeze the first item, so empty candidate list can be recognized & handled
        yield functools.reduce(older_pkg, packages, next(packages))
    except StopIteration:
        return
    # return sorted(packages, key=lambda pkg: pkg.timestamp)[:1]





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
    query = PackageQuery()
    for attr in arg_to_filter:
        query.add_package_filter(arg_to_filter[attr](kwargs[attr]))
    return query


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
