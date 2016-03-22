from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import functools
import os.path


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




# FIXME: PackageReference is currently broken - should it be dropped or fixed?
from .archive import Archive
class PackageReference(object):
    def __init__(self, package_reference):
        self.package_reference = package_reference

    @property
    def package(self):
        if os.path.isfile(self.package_reference):
            return Archive(self.package_reference)

        query = parse_package_spec(self.package_reference)
        # FIXME PackageReference.package
        raise LookupError(package_spec)
        return next(query.get_packages(env.get_repos()))

    @property
    def default_workspace(self):
        if os.path.isfile(self.package_reference):
            archive_filename = os.path.basename(self.package_reference)
            workspace_dir = os.path.splitext(archive_filename)[0]
        else:
            package_spec = parse_package_spec(self.package_reference)
            workspace_dir = package_spec.name
        return Workspace(workspace_dir)
