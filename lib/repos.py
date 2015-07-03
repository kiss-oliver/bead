from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


import os

from omlite import storable_pk_netaddrtime_uuid1 as storable
from omlite import Field
import omlite

from .pkg.archive import Archive
from .import tech
Path = tech.fs.Path


TEXT_FIELD = Field('VARCHAR NOT NULL')
UUID_FIELD = Field('VARCHAR NOT NULL')


@omlite.table_name('repositories')
@storable
class Repository(object):

    # id = UUID_FIELD
    name = TEXT_FIELD
    location = TEXT_FIELD

    # TODO: user maintained directory hierarchy

    def __init__(self, name=None, location=None):
        self.location = location
        self.name = name

    @property
    def directory(self):
        '''
        Location as a Path.

        Valid only for local repositories.
        '''
        return Path(self.location)

    def find_packages(self, uuid, version=None):
        # -> [Package]
        for name in os.listdir(self.directory):
            candidate = self.directory / name
            try:
                package = Archive(candidate)
                if package.uuid == uuid:
                    if version in (None, package.version):
                        yield package
            except:
                # ignore invalid packages
                # XXX - we should log them
                pass

    def find_newest(self, uuid):
        # -> Package
        newest = None
        for package in self.find_packages(uuid):
            if newest is None or package.timestamp > newest.timestamp:
                newest = package
        return newest

    def store(self, workspace, timestamp):
        # -> Package
        zipfilename = (
            self.directory / (
                '{package}_{timestamp}.zip'
                .format(
                    package=workspace.package_name,
                    timestamp=timestamp,
                )
            )
        )
        workspace.pack(zipfilename, timestamp=timestamp)
        return Archive(zipfilename)


def get_all():
    '''
    Iterator over Repositories
    '''
    ALL = '1 == 1'
    return omlite.filter(Repository, ALL)  # FIXME: implement omlite.all


def add(name, directory):
    repo = Repository(name, directory)
    omlite.save(repo)
