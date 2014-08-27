'''
Filesystem layout of packages
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os

from ..path import Path, ensure_directory
from .. import persistence
from .layouts import Workspace


def is_valid(dir):
    return all(
        (
            os.path.isdir(dir / Workspace.INPUT),
            os.path.isdir(dir / Workspace.OUTPUT),
            os.path.isdir(dir / Workspace.TEMP),
            os.path.isfile(dir / Workspace.PKGMETA),
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
    with open(pkg_path / Workspace.PKGMETA, 'w') as f:
        persistence.to_stream(pkgmeta, f)

    assert is_valid(pkg_path)


def create_directories(dir):
    pkg_path = Path(dir)
    ensure_directory(pkg_path)
    ensure_directory(pkg_path / Workspace.INPUT)
    ensure_directory(pkg_path / Workspace.OUTPUT)
    ensure_directory(pkg_path / Workspace.TEMP)


def get_package_name():
    return os.path.basename(os.getcwd())
