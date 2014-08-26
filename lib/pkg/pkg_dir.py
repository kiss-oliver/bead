'''
Filesystem layout of packages
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os

from .. import path
from .. import persistence

Path = path.Path

INPUT = Path('input')
OUTPUT = Path('output')
TEMP = Path('temp')
PKGMETA = '.pkgmeta'


def is_valid(dir):
    return all(
        (
            os.path.isdir(dir / INPUT),
            os.path.isdir(dir / OUTPUT),
            os.path.isdir(dir / TEMP),
            os.path.isfile(dir / PKGMETA),
        )
    )


def create(dir):
    '''
    Set up an empty project structure.

    Works with either an empty directory or a directory to be created.
    '''
    try:
        assert os.listdir(dir) == []
    except OSError:
        pass

    pkg_path = Path(dir)
    create_directories(pkg_path)

    pkgmeta = {}  # TODO
    with open(pkg_path / PKGMETA, 'w') as f:
        persistence.to_stream(pkgmeta, f)

    assert is_valid(pkg_path)


def create_directories(dir):
    pkg_path = Path(dir)
    path.ensure_directory(pkg_path)
    path.ensure_directory(pkg_path / INPUT)
    path.ensure_directory(pkg_path / OUTPUT)
    path.ensure_directory(pkg_path / TEMP)


def get_package_name():
    return os.path.basename(os.getcwd())
