'''
Public interface:

Peer.self() -> special peer referring to local self
Peer.by_name(name)
peer.save()
 - peer.rename(old_name, new_name)
Peer.exists(name)
peer.export(filename)
Peer.import(filename, peer_name)

peer.knows_about(name)
peer.get_translation(name)

add_translation(name, package_uuid)
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os

from omlite import storable_pk_netaddrtime_uuid1 as storable
from omlite import sql_constraint
from omlite import Field
import omlite

TEXT_FIELD = Field('VARCHAR NOT NULL')
UUID_FIELD = Field('VARCHAR NOT NULL')


@storable
class Peer(object):

    id = UUID_FIELD
    name = Field('VARCHAR NOT NULL UNIQUE')

    #
    def __init__(self, name=None, id=None):
        self.name = name
        self.id = id

    def save(self):
        omlite.save(self)

    @classmethod
    def by_name(cls, name):
        peers = list(omlite.filter(cls, 'name = ?', name))
        assert len(peers) <= 1

        if peers:
            return peers[0]
        raise LookupError(cls, name)

    @classmethod
    def self(cls):
        '''
        Return special Peer referring to the user.
        '''
        return cls.by_name('')

    def get_translation(self, package_name):
        translations = list(
            omlite.filter(
                Translation,
                'peer_id = ? AND name = ?',
                self.id, package_name))
        assert len(translations) <= 1

        if translations:
            return translations[0]
        raise LookupError(self.name, package_name)

    def knows_about(self, package_name):
        try:
            self.get_translation(package_name)
            return True
        except LookupError:
            return False

    def export(self, filename):
        Exporter(self, filename).export()


@sql_constraint('FOREIGN KEY (peer_id) REFERENCES peers(id) ON DELETE CASCADE')
@sql_constraint('UNIQUE (peer_id, name)')
@storable
class Translation(object):

    id = UUID_FIELD  # for high probability collision free export-import
    peer_id = UUID_FIELD
    name = TEXT_FIELD
    package_uuid = UUID_FIELD


def add_translation(name, uuid):
    ''' Registers `name` as a local name for package identified by `uuid`.
    '''
    self = Peer.self()
    translation = Translation()
    translation.peer_id = self.id
    translation.name = name
    translation.package_uuid = uuid
    omlite.save(translation)


EXPORT_VERSION = 'version 1'
EXPORT_META_ID = 1


def _export_meta_class(db):
    @omlite.database(db)
    @sql_constraint('CHECK (id == {})'.format(EXPORT_META_ID))
    @omlite.table_name('meta')
    @storable
    class Meta(object):
        ''' A single row table describing what is exported and how
        '''
        id = UUID_FIELD
        peer_id = UUID_FIELD
        version = TEXT_FIELD
        # date_exported?
    return Meta


def _exported_translation_class(db):
    @omlite.database(db)
    @sql_constraint('UNIQUE (name)')
    @storable
    class ExportedTranslation(object):
        id = UUID_FIELD
        name = TEXT_FIELD
        package_uuid = UUID_FIELD

        @classmethod
        def from_translation(cls, translation):
            exportable = cls()
            exportable.id = translation.id
            exportable.name = translation.name
            exportable.package_uuid = translation.package_uuid
            return exportable

        def to_translation(self):
            translation = Translation()
            translation.id = self.id
            translation.name = self.name
            translation.package_uuid = self.package_uuid
            return translation

    return ExportedTranslation


class Exporter(object):

    def __init__(self, peer, filename):
        self.peer = peer
        self.filename = filename

    def _init_export_db(self, export_db):
        Meta = _export_meta_class(export_db)
        omlite.create_table(Meta)
        meta = Meta()
        meta.id = EXPORT_META_ID
        meta.version = EXPORT_VERSION
        meta.peer_id = self.peer.id
        omlite.create(meta)

        ExportedTranslation = _exported_translation_class(export_db)
        omlite.create_table(ExportedTranslation)

    def export(self):
        export_db = omlite.Database(self.filename)
        self._init_export_db(export_db)

        ExportedTranslation = _exported_translation_class(export_db)
        translations = omlite.filter(Translation, 'peer_id == ?', self.peer.id)
        for translation in translations:
            omlite.create(ExportedTranslation.from_translation(translation))


def import_translations(peer_name, filename):
    Importer(peer_name, filename).import_translations()


class Importer(object):

    def __init__(self, peer_name, filename):
        self.peer_name = peer_name
        self.filename = filename

    def import_translations(self):
        assert os.path.isfile(self.filename)
        import_db = omlite.Database(self.filename)

        imported_peer = self._get_peer_to_import(import_db)
        omlite.delete(imported_peer)
        # FIXME?: omlite should not erase id on delete
        imported_peer = self._get_peer_to_import(import_db)
        omlite.create(imported_peer)

        ExportedTranslation = _exported_translation_class(import_db)
        exported_translations = omlite.filter(ExportedTranslation, '1 == 1')
        for exported_translation in exported_translations:
            translation = exported_translation.to_translation()
            translation.peer_id = imported_peer.id
            omlite.create(translation)

    def _get_peer_to_import(self, db):
        Meta = _export_meta_class(db)
        meta = omlite.get(Meta, EXPORT_META_ID)
        assert meta.version == EXPORT_VERSION
        imported_peer = Peer()
        imported_peer.id = meta.peer_id
        imported_peer.name = self.peer_name
        return imported_peer
