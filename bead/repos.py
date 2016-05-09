'''
We are responsible to store (and retrieve) packages.
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


import bisect
from datetime import datetime, timedelta
import functools
from glob import iglob
import os

from .pkg.archive import Archive
from .pkg import spec as pkg_spec
from .tech import persistence
from .tech.timestamp import time_from_timestamp
from .import tech
Path = tech.fs.Path


# FIXME: create environment module
ENV_REPOS = 'repositories'
REPO_NAME = 'name'
REPO_LOCATION = 'directory'


class Environment:

    def __init__(self, filename):
        self.filename = filename
        self._content = {}

    def load(self):
        with open(self.filename, 'r') as f:
            self._content = persistence.load(f)

    def save(self):
        with open(self.filename, 'w') as f:
            persistence.dump(self._content, f)

    def get_repos(self):
        for repo_spec in self._content.get(ENV_REPOS, ()):
            repo = Repository(
                repo_spec.get(REPO_NAME),
                repo_spec.get(REPO_LOCATION))
            yield repo

    def set_repos(self, repos):
        self._content[ENV_REPOS] = [
            {
                REPO_NAME: repo.name,
                REPO_LOCATION: repo.location
            }
            for repo in repos]


env = None


def initialize(config_dir):
    try:
        os.makedirs(config_dir)
    except OSError:
        assert os.path.isdir(config_dir)
    global env
    env_path = Path(config_dir) / 'env.json'
    env = Environment(env_path)
    if os.path.exists(env_path):
        env.load()


class _Wrapper(object):
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __eq__(self, other):
        return self.wrapped.timestamp == other.wrapped.timestamp


@functools.total_ordering
class _MoreIsLess(_Wrapper):
    def __lt__(self, other):
        return self.wrapped.timestamp > other.wrapped.timestamp


@functools.total_ordering
class _LessIsLess(_Wrapper):
    def __lt__(self, other):
        return self.wrapped.timestamp < other.wrapped.timestamp


def order_and_limit_packages(packages, order=pkg_spec.NEWEST_FIRST, limit=None):
    '''
    Order packages by timestamps and keep only the closest ones.
    '''
    # wrap packages so that they can be compared by timestamps
    compare_wrap = {
        pkg_spec.NEWEST_FIRST: _MoreIsLess,
        pkg_spec.OLDEST_FIRST: _LessIsLess,
    }[order]
    comparable_packages = (compare_wrap(pkg) for pkg in packages)

    if limit:
        # assume we have lots of packages, so do it with memory limited
        # XXX: heapq might be faster a bit?
        wrapped_results = []
        for pkg in comparable_packages:
            bisect.insort_right(wrapped_results, pkg)
            if len(wrapped_results) > limit:
                del wrapped_results[limit]
    else:
        wrapped_results = sorted(comparable_packages)

    # unwrap wrapped_results
    return [wrapper.wrapped for wrapper in wrapped_results]


class Repository(object):
    # TODO: user maintained directory hierarchy

    def __init__(self, name=None, location=None):
        self.location = location
        self.name = name

    @property
    def directory(self):
        '''
        Location as a Path.

        Valid only for local repositories.
        '''
        return Path(self.location)

    def find_packages(self, conditions, order=pkg_spec.NEWEST_FIRST, limit=None):
        '''
        Retrieve matching packages.

        (future possibility), it might run in another process,
        potentially on another machine, so it might be faster to restrict
        the results here and not send the whole list over the network.
        '''
        match = pkg_spec.compile_conditions(conditions)

        # FUTURE IMPLEMENTATIONS: check for bead_uuid & content hash
        # they are good candidates for indexing
        package_name_globs = [
            value
            for tag, value in conditions
            if tag == pkg_spec.PACKAGE_NAME_GLOB]
        if package_name_globs:
            glob = package_name_globs[0] + '*'
        else:
            glob = '*'

        # XXX: directory itself might be a pattern - is it OK?
        paths = iglob(self.directory / glob)
        # FIXME: Repository.find_packages dies on non package in the directory
        packages = (Archive(path, self.name) for path in paths)
        candidates = (pkg for pkg in packages if match(pkg))

        # FUTURE IMPLEMENTATIONS: can there be more than one valid match?
        return order_and_limit_packages(candidates, order, limit)

    def store(self, workspace, timestamp):
        # -> Package
        zipfilename = (
            self.directory / (
                '{package_name}_{timestamp}.zip'
                .format(
                    package_name=workspace.package_name,
                    timestamp=timestamp)))
        workspace.pack(zipfilename, timestamp=timestamp)
        return Archive(zipfilename)

    def find_names(self, bead_uuid, content_hash, timestamp):
        '''
        -> (exact_match, best_guess, best_guess_timestamp, names)
        where
            exact_match          = name (bead_uuid & content_hash matched)
            best_guess           = name (bead_uuid matched, timestamp is closest to input's)
            best_guess_timestamp = timestamp ()
            names                = sequence of names (bead_uuid matched)
        '''
        assert isinstance(timestamp, datetime)
        paths = (self.directory / fname for fname in os.listdir(self.directory))
        # FIXME: Repository.find_names dies on non package in the directory
        packages = (Archive(path, self.name) for path in paths)
        candidates = (pkg for pkg in packages if pkg.uuid == bead_uuid)

        exact_match          = None
        best_guess           = None
        best_guess_timestamp = None
        best_guess_timedelta = None
        names                = set()
        for pkg in candidates:
            if pkg.version == content_hash:
                exact_match = pkg.name
            #
            pkg_timestamp = time_from_timestamp(pkg.timestamp_str)
            pkg_timedelta = pkg_timestamp - timestamp
            if pkg_timedelta < timedelta():
                pkg_timedelta = -pkg_timedelta
            if (
                (best_guess_timedelta is None) or
                (pkg_timedelta < best_guess_timedelta) or
                (pkg_timedelta == best_guess_timedelta and pkg_timestamp > best_guess_timestamp)
            ):
                best_guess = pkg.name
                best_guess_timestamp = pkg_timestamp
                best_guess_timedelta = pkg_timedelta
            #
            names.add(pkg.name)

        return exact_match, best_guess, best_guess_timestamp, names


def get(name):
    '''
    Return repository having :name or None.
    '''
    for repo in env.get_repos():
        if repo.name == name:
            return repo


def is_known(name):
    return get(name) is not None


def add(name, directory):
    repos = list(env.get_repos())
    # check unique repo
    for repo in repos:
        if repo.name == name:
            raise ValueError(
                'Repository with name {} already exists'.format(name))
        if repo.location == directory:
            raise ValueError(
                'Repository with location {} already exists'
                .format(repo.location))

    env.set_repos(repos + [Repository(name, directory)])
    env.save()


def forget(name):
    env.set_repos(
        repo
        for repo in env.get_repos()
        if repo.name != name)
    env.save()


# FIXME: move get_package to Environment.get_package
def get_package(bead_uuid, content_hash):
    query = ((pkg_spec.PACKAGE_UUID, bead_uuid), (pkg_spec.CONTENT_HASH, content_hash))
    for repo in env.get_repos():
        for package in repo.find_packages(query):
            return package
    raise LookupError('Package {} {} not found'.format(bead_uuid, content_hash))
