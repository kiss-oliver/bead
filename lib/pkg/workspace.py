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
from . import layouts


class Workspace(object):

    def __init__(self, directory):
        self.directory = Path(os.path.abspath(directory))

    @property
    def is_valid(self):
        dir = self.directory
        return all(
            (
                os.path.isdir(dir / layouts.Workspace.INPUT),
                os.path.isdir(dir / layouts.Workspace.OUTPUT),
                os.path.isdir(dir / layouts.Workspace.TEMP),
                os.path.isfile(dir / layouts.Workspace.PKGMETA),
            )
        )

    def create(self):
        '''
        Set up an empty project structure.

        Works with either an empty directory or a directory to be created.
        '''
        dir = self.directory
        try:
            assert os.listdir(dir) == []
        except OSError:
            pass

        self.create_directories()

        pkgmeta = {}  # TODO
        with open(dir / layouts.Workspace.PKGMETA, 'w') as f:
            persistence.to_stream(pkgmeta, f)

        assert self.is_valid

    def create_directories(self):
        dir = self.directory
        ensure_directory(dir)
        ensure_directory(dir / layouts.Workspace.INPUT)
        ensure_directory(dir / layouts.Workspace.OUTPUT)
        ensure_directory(dir / layouts.Workspace.TEMP)

    @property
    def package_name(self):
        return os.path.basename(self.directory)
