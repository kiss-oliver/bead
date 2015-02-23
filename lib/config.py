from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
from . import PACKAGE
from . import tech

Path = tech.fs.Path

CONFIG_FILE_NAME = 'config.json'
PACKAGES_DB_FILE_NAME = 'packages.sqlite3'
XDG_CONFIG_HOME = 'XDG_CONFIG_HOME'

# personal-uuid identifies *me* the user and differentiates from my peers
KEY_PERSONAL_ID = 'personal-id'


def get_config_dir_path():
    home_config = Path(os.path.expanduser('~/.config'))
    config_path = (
        Path(os.environ.get(XDG_CONFIG_HOME, home_config)) / PACKAGE)
    return config_path


def get_path(config_file):
    return get_config_dir_path() / config_file


def ensure_config_dir():
    '''Ensures that the configuration exists and is valid.

    Creates the necessary files if needed.
    '''
    config_dir = get_config_dir_path()
    tech.fs.ensure_directory(config_dir)
    config_path = get_path(CONFIG_FILE_NAME)
    if not os.path.exists(config_path):
        config = {
            KEY_PERSONAL_ID: tech.identifier.uuid(),
        }
        save(config)


def load():
    config_path = get_path(CONFIG_FILE_NAME)
    with open(config_path, 'r') as f:
        return tech.persistence.load(f)


def save(config):
    config_path = get_path(CONFIG_FILE_NAME)
    with open(config_path, 'w') as f:
        tech.persistence.dump(config, f)


def get_personal_id():
    config = load()
    return config[KEY_PERSONAL_ID]
