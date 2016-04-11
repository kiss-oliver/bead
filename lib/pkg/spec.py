from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import functools


# QUERY_ORDER:
NEWEST_FIRST = 'newest_first'
OLDEST_FIRST = 'oldest_first'
UNSORTED     = 'unsorted'

# QUERY_WHERE:
OLDER_THAN               = 'OLDER_THAN'
NEWER_THAN               = 'NEWER_THAN'
PACKAGE_NAME_GLOB        = 'PACKAGE_NAME_GLOB'
PACKAGE_UUID             = 'PACKAGE_UUID'
CONTENT_HASH             = 'CONTENT_HASH'


# private and specific to Repository implementation, when Repository gains
# more power, it should change how it handles queries (e.g. using PACKAGE_UUID
# or CONTENT_HASH directly through an index)

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
            for repo in repositories
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
    def _add_repo_query(self, pkg_query):
        '''
            Use :pkg_query: for querying repos for package candidates.
        '''
        self.repo_queries.append(pkg_query)

    def _add_package_filter(self, pkg_filter):
        '''
            Restrict packages to those matching :pkg_filter:
        '''
        self.package_filters.append(pkg_filter)

    def _add_match_reducer(self, match_reducer):
        '''
            Reduce matches - keep only the best one[s]
        '''
        self.match_reducers.append(match_reducer)

    # repo queries
    def by_name(self, package_name):
        def query(repo):
            return repo.all_by_name(package_name)
        self._add_repo_query(query)
        return self

    def by_uuid(self, package_uuid, content_hash=None):
        def query(repo):
            return repo.all_by_uuid(package_uuid, content_hash)
        self._add_repo_query(query)
        return self

    # package filters
    def is_newer_than(self, timestamp):
        def filter(pkg):
            return pkg.timestamp > timestamp
        self._add_package_filter(filter)
        return self

    def is_older_than(self, timestamp):
        def filter(pkg):
            return pkg.timestamp < timestamp
        self._add_package_filter(filter)
        return self

    def has_content_prefix(self, hash_prefix):
        def filter(pkg):
            return pkg.version.startswith(hash_prefix)
        self._add_package_filter(filter)
        return self

    def has_timestamp_prefix(self, timestamp_str):
        def filter(pkg):
            return pkg.timestamp_str.startswith(timestamp_str)
        self._add_package_filter(filter)
        return self

    # match reducers
    def keep_newest(self):
        self._add_match_reducer(newest)
        return self

    def keep_oldest(self):
        self._add_match_reducer(oldest)
        return self


# match reducers
def newest(packages):
    newer_pkg = functools.partial(max, key=lambda pkg: pkg.timestamp)
    try:
        # squeze the first item,
        # so empty candidate list can be recognized & handled
        yield functools.reduce(newer_pkg, packages, next(packages))
    except StopIteration:
        return
    # return sorted(packages, key=lambda pkg: pkg.timestamp, reverse=True)[:1]


def oldest(packages):
    older_pkg = functools.partial(min, key=lambda pkg: pkg.timestamp)
    try:
        # squeze the first item,
        # so empty candidate list can be recognized & handled
        yield functools.reduce(older_pkg, packages, next(packages))
    except StopIteration:
        return
    # return sorted(packages, key=lambda pkg: pkg.timestamp)[:1]


# FIXME: selecting packages from repositories matching a query should be the responsibility of class Repository!
# this implies, that the above query should become hidden and queries should be described as data (e.g. a dictionary)
