import os
import pathlib
import re

from cached_property import cached_property

from tracelog import TRACELOG
from .bead import UnpackableBead
from . import meta
from . import tech

from .ziparchive import ZipArchive
from .exceptions import InvalidArchive

persistence = tech.persistence

__all__ = ('Archive', 'InvalidArchive')


CACHE_CONTENT_ID = 'content_id'
CACHE_INPUT_MAP = 'input_map'


def cached_attribute(cache_key, ziparchive_attribute):
    """Make a cache accessor @property with a self.ziparchive.attribute fallback
    """
    @property
    def maybe_cached_attr(self):
        try:
            return self.cache[cache_key]
        except LookupError:
            return getattr(self.ziparchive, ziparchive_attribute)
    return maybe_cached_attr


class Archive(UnpackableBead):
    def __init__(self, filename, box_name=''):
        self.archive_filename = filename
        self.box_name = box_name
        self.name = bead_name_from_file_path(filename)
        self.cache = ArchiveCache(self.archive_filename)

        # check that we can get access to metadata
        # the resulting archive can still be invalid and die unexpectedly later with
        # InvalidArchive exception, as these are potentially cached values
        # to make the check cheap if needed
        self.meta_version
        self.timestamp
        self.kind

    meta_version = cached_attribute(meta.META_VERSION, 'meta_version')
    content_id = cached_attribute(CACHE_CONTENT_ID, 'content_id')
    kind = cached_attribute(meta.KIND, 'kind')
    timestamp_str = cached_attribute(meta.FREEZE_TIME, 'timestamp_str')
    input_map = cached_attribute(CACHE_INPUT_MAP, 'input_map')

    @cached_property
    def ziparchive(self):
        # FIXME: verify ziparchive compatibility with archivecache
        # TODO: populate cache from archive
        return ZipArchive(self.archive_filename, self.box_name)

    @property
    def is_valid(self):
        # TODO: verify that cache matches ziparchive
        return self.ziparchive.is_valid

    @property
    def inputs(self):
        try:
            return tuple(meta.parse_inputs({meta.INPUTS: self.cache[meta.INPUTS]}))
        except LookupError:
            return self.ziparchive.inputs

    def extract_dir(self, zip_dir, fs_dir):
        return self.ziparchive.extract_dir(zip_dir, fs_dir)

    def extract_file(self, zip_path, fs_path):
        return self.ziparchive.extract_file(zip_path, fs_path)

    def unpack_code_to(self, fs_dir):
        self.ziparchive.unpack_code_to(fs_dir)

    def unpack_data_to(self, fs_dir):
        self.ziparchive.unpack_data_to(fs_dir)

    def unpack_meta_to(self, workspace):
        self.ziparchive.unpack_meta_to(workspace)


class ArchiveCache:
    def __init__(self, archive_filename):
        self.values = {}
        self.archive_path = pathlib.Path(archive_filename)
        self.load()

    @property
    def cache_path(self):
        if self.archive_path.suffix != 'zip':
            raise FileNotFoundError(f'Archive can not have cache {self.archive_path}')

        return self.archive_path.with_suffix('meta')

    def load(self):
        try:
            try:
                self.values = persistence.loads(self.cache_path.read_text())
            except persistence.ReadError:
                TRACELOG(f"Ignoring existing, malformed bead meta cache {self.cache_path}")
        except FileNotFoundError:
            pass

    def save(self):
        try:
            self.cache_path.write_text(persistence.dumps(self.values))
        except FileNotFoundError:
            pass

    def __getitem__(self, key):
        return self.values[key]


def bead_name_from_file_path(path):
    '''
    Parse bead name from a file path.

    Might return a simpler name than intended
    '''
    name_with_timestamp, ext = os.path.splitext(os.path.basename(path))
    # assert ext == '.zip'  # not enforced to allow having beads with different extensions
    name = re.sub('_[0-9]{8}(?:[tT][-+0-9]*)?$', '', name_with_timestamp)
    return name


assert 'bead-2015v3' == bead_name_from_file_path('bead-2015v3.zip')
assert 'bead-2015v3' == bead_name_from_file_path('bead-2015v3_20150923.zip')
assert 'bead-2015v3' == bead_name_from_file_path('bead-2015v3_20150923T010203012345+0200.zip')
assert 'bead-2015v3' == bead_name_from_file_path('bead-2015v3_20150923T010203012345-0200.zip')
assert 'bead-2015v3' == bead_name_from_file_path('path/to/bead-2015v3_20150923.zip')
