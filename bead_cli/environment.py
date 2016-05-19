'''
User specific environment
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from bead.repos import Repository
from bead.tech import persistence
import bead.spec as bead_spec
import os

ENV_REPOS = 'repositories'
REPO_NAME = 'name'
REPO_LOCATION = 'directory'


class Environment:

    def __init__(self, filename):
        self.filename = filename
        self._content = {}
        if os.path.exists(self.filename):
            self.load()

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

    def add_repo(self, name, directory):
        repos = list(self.get_repos())
        # check unique repo
        for repo in repos:
            if repo.name == name:
                raise ValueError(
                    'Repository with name {} already exists'.format(name))
            if repo.location == directory:
                raise ValueError(
                    'Repository with location {} already exists'
                    .format(repo.location))

        self.set_repos(repos + [Repository(name, directory)])

    def forget_repo(self, name):
        self.set_repos(
            repo
            for repo in self.get_repos()
            if repo.name != name)

    def get_repo(self, name):
        '''
        Return repository having :name or None.
        '''
        for repo in self.get_repos():
            if repo.name == name:
                return repo

    def is_known_repo(self, name):
        return self.get_repo(name) is not None

    def get_bead(self, bead_uuid, content_hash):
        query = ((bead_spec.BEAD_UUID, bead_uuid), (bead_spec.CONTENT_HASH, content_hash))
        for repo in self.get_repos():
            for bead in repo.find_beads(query):
                return bead
        raise LookupError('Bead {} {} not found'.format(bead_uuid, content_hash))
