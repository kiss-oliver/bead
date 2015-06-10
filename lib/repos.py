from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


import os

from .pkg.archive import Archive
from .import tech
Path = tech.fs.Path


class Repository(object):

    def find_package(self, uuid, version=None):
        # -> [Package]
        pass

    def find_newest(self, uuid):
        # -> Package
        pass

    def store(self, workspace, timestamp):
        # -> Package
        pass


class UserManagedDirectory(Repository):

    # TODO: user maintained directory hierarchy

    def __init__(self, directory):
        self.directory = Path(directory)

    def find_package(self, uuid, version=None):
        # -> [Package]
        for name in os.listdir(self.directory):
            candidate = self.directory / name
            try:
                package = Archive(candidate)
                if package.uuid == uuid:
                    if version in (None, package.version):
                        return package
            except:
                pass
