'''
We are responsible to store (and retrieve) packages.
'''

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


@omlite.sql_constraint('UNIQUE (name)')
@omlite.sql_constraint('UNIQUE (location)')
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

    def store(self, workspace, timestamp):
        # -> Package
        zipfilename = (
            self.directory / (
                '{package}_{timestamp}.zip'
                .format(
                    package=workspace.package_name,
                    timestamp=timestamp)))
        workspace.pack(zipfilename, timestamp=timestamp)
        return Archive(zipfilename)


def get(name):
    '''
    Return repository having :name or None.
    '''
    for repo in omlite.filter(Repository, 'name=?', name):
        return repo


def is_known(name):
    return get(name) is not None


def get_all():
    return omlite.get_all(Repository)


def add(name, directory):
    repo = Repository(name, directory)
    try:
        omlite.save(repo)
    except omlite.IntegrityError as e:
        raise ValueError(e)


def forget(name):
    repo = get(name)
    omlite.delete(repo)


def get_package(uuid, version):
    for repo in get_all():
        for package in repo.find_packages(uuid, version):
            return package
    raise LookupError('Package {} {} not found'.format(uuid, version))
