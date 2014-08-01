'''
Filesystem layout of packages
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os

from .. import path
from . import pkg_zip

INPUT = 'input'
OUTPUT = 'output'
TEMP = 'temp'
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
    path.ensure_directory(dir)
    assert os.listdir(dir) == []

    pkg_path = path.Path(dir)
    os.mkdir(pkg_path / INPUT)
    os.mkdir(pkg_path / OUTPUT)
    os.mkdir(pkg_path / TEMP)
    path.write_file(pkg_path / PKGMETA, pkg_zip.to_yaml({}))

    assert is_valid(pkg_path)
