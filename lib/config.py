from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from appdirs import user_config_dir
import os
from . import PACKAGE
from . import tech

Path = tech.fs.Path

CONFIG_FILE_NAME = 'config.json'
PACKAGES_DB_FILE_NAME = 'packages.sqlite3'

# personal-uuid identifies *me* the user and differentiates from my peers
KEY_PERSONAL_ID = 'personal-id'
KEY_REPOSITORIES = 'repositories'
KEY_DEFAULT_STORE_REPOSITORY = 'default store repository'


class Config(object):

    config = dict
    config_path = str

    def __init__(self):
        self.root = Path(user_config_dir(PACKAGE))
        self.config_path = self.path_to(CONFIG_FILE_NAME)
        self._ensure_config_dir()
        self.config = self.load()

    def _ensure_config_dir(self):
        # Ensures that the configuration exists and is valid.
        #
        # Creates the necessary files if needed.
        tech.fs.ensure_directory(self.root)
        if not os.path.exists(self.config_path):
            self.config = {
                KEY_PERSONAL_ID: tech.identifier.uuid(),
                KEY_REPOSITORIES: [],
                KEY_DEFAULT_STORE_REPOSITORY: None,
            }
            self.save()

    def load(self):
        with open(self.config_path, 'r') as f:
            return tech.persistence.load(f)

    def save(self):
        with open(self.config_path, 'w') as f:
            tech.persistence.dump(self.config, f)

    def path_to(self, file):
        return self.root / file

    @property
    def personal_id(self):
        return self.config[KEY_PERSONAL_ID]

    @property
    def repositories(self):
        return self.config[KEY_REPOSITORIES]

    @property
    def default_store_repository(self):
        return self.config[KEY_DEFAULT_STORE_REPOSITORY]

    @default_store_repository.setter
    def default_store_repository(self, repository):
        self.config[KEY_DEFAULT_STORE_REPOSITORY] = repository
