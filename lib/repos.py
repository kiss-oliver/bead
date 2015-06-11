from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


import os

from omlite import storable_pk_netaddrtime_uuid1 as storable
from omlite import sql_constraint
from omlite import Field
import omlite

from .pkg.archive import Archive
from .import tech
Path = tech.fs.Path


TEXT_FIELD = Field('VARCHAR NOT NULL')
UUID_FIELD = Field('VARCHAR NOT NULL')


@storable
class Repository(object):

    # id = UUID_FIELD
    name = TEXT_FIELD
    location = TEXT_FIELD

    def __init__(self, name=None, location=None):
        self.location = location
        self.name = name
        self._impl = UserManagedDirectory()

    def find_package(self, uuid, version=None):
        # -> [Package]
        return self._impl.find_package(self, uuid, version)

    def find_newest(self, uuid):
        # -> Package
        return self._impl.find_newest(self, uuid)

    def store(self, workspace, timestamp):
        # -> Package
        return self._impl.store(self, workspace, timestamp)


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

# FIXME: remove workspace.flat_repo
