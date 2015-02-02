from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
from . import PACKAGE
from . import tech

Path = tech.fs.Path

CONFIG_FILE_NAME = 'config.json'
XDG_CONFIG_HOME = 'XDG_CONFIG_HOME'


def get_config_dir_path():
    home_config = Path(os.path.expanduser('~/.config'))
    config_path = (
        Path(os.environ.get(XDG_CONFIG_HOME, home_config)) / PACKAGE)
    return config_path


def get_path(config_file):
    return get_config_dir_path() / config_file


def ensure_config_dir():
    tech.fs.ensure_directory(get_config_dir_path())


def load():
    try:
        with open(get_path(CONFIG_FILE_NAME), 'r') as f:
            return tech.persistence.load(f)
    except IOError:
        # TODO: return a valid configuration (e.g. personal-uuid pre=filled)
        return {}


def save(config):
    config_path = get_path(CONFIG_FILE_NAME)
    tech.fs.ensure_directory(tech.fs.parent(config_path))
    with open(config_path, 'w') as f:
        tech.persistence.dump(config, f)
