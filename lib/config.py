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


class Config(object):

    '''
    Persistent key-value store for user configs as a context manager
    '''

    __slots__ = ('_dict', '_copy')

    def __init__(self):
        self._dict = {}
        self._copy = None

    def __enter__(self):
        def load_config():
            try:
                with open(get_path(CONFIG_FILE_NAME), 'r') as f:
                    return f.read()
            except IOError:
                return '{}'

        config = load_config()
        self._dict = tech.persistence.loads(config)
        self._copy = tech.persistence.loads(config)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._copy != self._dict:
            self._copy = None
            config_path = get_path(CONFIG_FILE_NAME)
            tech.fs.ensure_directory(tech.fs.parent(config_path))
            with open(config_path, 'w') as f:
                tech.persistence.dump(self._dict, f)

    def __getattr__(self, attr):
        try:
            return self._dict[attr]
        except KeyError:
            # python 3.4 is picky
            # 2.7 and pypy is fine without changing the exception type
            raise AttributeError

    def __setattr__(self, attr, value):
        if attr in self.__slots__:
            object.__setattr__(self, attr, value)
        else:
            self._dict[attr] = value

    def __getitem__(self, item):
        return self._dict[item]

    def __setitem__(self, key, value):
        self._dict[key] = value
