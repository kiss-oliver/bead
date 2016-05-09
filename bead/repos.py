'''
We are responsible to store (and retrieve) beads.
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

from .archive import Archive
from . import spec as bead_spec
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


def order_and_limit_beads(beads, order=bead_spec.NEWEST_FIRST, limit=None):
    '''
    Order beads by timestamps and keep only the closest ones.
    '''
    # wrap beads so that they can be compared by timestamps
    compare_wrap = {
        bead_spec.NEWEST_FIRST: _MoreIsLess,
        bead_spec.OLDEST_FIRST: _LessIsLess,
    }[order]
    comparable_beads = (compare_wrap(bead) for bead in beads)

    if limit:
        # assume we have lots of beads, so do it with memory limited
        # XXX: heapq might be faster a bit?
        wrapped_results = []
        for bead in comparable_beads:
            bisect.insort_right(wrapped_results, bead)
            if len(wrapped_results) > limit:
                del wrapped_results[limit]
    else:
        wrapped_results = sorted(comparable_beads)

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

    def find_beads(self, conditions, order=bead_spec.NEWEST_FIRST, limit=None):
        '''
        Retrieve matching beads.

        (future possibility), it might run in another process,
        potentially on another machine, so it might be faster to restrict
        the results here and not send the whole list over the network.
        '''
        match = bead_spec.compile_conditions(conditions)

        # FUTURE IMPLEMENTATIONS: check for bead_uuid & content hash
        # they are good candidates for indexing
        bead_name_globs = [
            value
            for tag, value in conditions
            if tag == bead_spec.BEAD_NAME_GLOB]
        if bead_name_globs:
            glob = bead_name_globs[0] + '*'
        else:
            glob = '*'

        # XXX: directory itself might be a pattern - is it OK?
        paths = iglob(self.directory / glob)
        # FIXME: Repository.find_beads dies on non bead in the directory
        beads = (Archive(path, self.name) for path in paths)
        candidates = (bead for bead in beads if match(bead))

        # FUTURE IMPLEMENTATIONS: can there be more than one valid match?
        return order_and_limit_beads(candidates, order, limit)

    def store(self, workspace, timestamp):
        # -> Bead
        zipfilename = (
            self.directory / (
                '{bead_name}_{timestamp}.zip'
                .format(
                    bead_name=workspace.bead_name,
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
        # FIXME: Repository.find_names dies on non bead in the directory
        beads = (Archive(path, self.name) for path in paths)
        candidates = (bead for bead in beads if bead.bead_uuid == bead_uuid)

        exact_match          = None
        best_guess           = None
        best_guess_timestamp = None
        best_guess_timedelta = None
        names                = set()
        for bead in candidates:
            if bead.content_hash == content_hash:
                exact_match = bead.name
            #
            bead_timestamp = time_from_timestamp(bead.timestamp_str)
            bead_timedelta = bead_timestamp - timestamp
            if bead_timedelta < timedelta():
                bead_timedelta = -bead_timedelta
            if (
                (best_guess_timedelta is None) or
                (bead_timedelta < best_guess_timedelta) or
                (bead_timedelta == best_guess_timedelta and bead_timestamp > best_guess_timestamp)
            ):
                best_guess = bead.name
                best_guess_timestamp = bead_timestamp
                best_guess_timedelta = bead_timedelta
            #
            names.add(bead.name)

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


# FIXME: move get_bead to Environment.get_bead
def get_bead(bead_uuid, content_hash):
    query = ((bead_spec.BEAD_UUID, bead_uuid), (bead_spec.CONTENT_HASH, content_hash))
    for repo in env.get_repos():
        for bead in repo.find_beads(query):
            return bead
    raise LookupError('Bead {} {} not found'.format(bead_uuid, content_hash))
