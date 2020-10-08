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


def _cached_zip_attribute(cache_key: str, ziparchive_attribute):
    """Make a cache accessor @property with a self.ziparchive.attribute fallback

    raises InvalidArchive if the attribute is not cached
        and the backing ziparchive is not valid.
    """
    def maybe_cached_attr(self):
        try:
            return self.cache[cache_key]
        except LookupError:
            return getattr(self.ziparchive, ziparchive_attribute)
    return property(maybe_cached_attr)


class Archive(UnpackableBead):
    def __init__(self, filename, box_name=''):
        self.archive_filename = filename
        self.archive_path = pathlib.Path(filename)
        self.box_name = box_name
        self.name = bead_name_from_file_path(filename)
        self.cache = {}
        self.load_cache()

        # Check that we can get access to metadata
        #  - either through the cache or through the archive
        # The resulting archive can still be invalid and die unexpectedly later with
        # InvalidArchive exception, as these are potentially cached values
        self.meta_version
        self.timestamp
        self.kind

    def load_cache(self):
        try:
            try:
                self.cache = persistence.loads(self.cache_path.read_text())
            except persistence.ReadError:
                TRACELOG(f"Ignoring existing, malformed bead meta cache {self.cache_path}")
        except FileNotFoundError:
            pass

    def save_cache(self):
        try:
            self.cache_path.write_text(persistence.dumps(self.cache))
        except FileNotFoundError:
            pass

    @property
    def cache_path(self):
        if self.archive_path.suffix != '.zip':
            raise FileNotFoundError(f'Archive can not have cache {self.archive_path}')

        return self.archive_path.with_suffix('.xmeta')

    meta_version = _cached_zip_attribute(meta.META_VERSION, 'meta_version')
    content_id = _cached_zip_attribute(CACHE_CONTENT_ID, 'content_id')
    kind = _cached_zip_attribute(meta.KIND, 'kind')
    timestamp_str = _cached_zip_attribute(meta.FREEZE_TIME, 'timestamp_str')

    @property
    def input_map(self):
        try:
            return self.cache[CACHE_INPUT_MAP]
        except LookupError:
            return self.ziparchive.input_map

    @input_map.setter
    def input_map(self, input_map):
        self.cache[CACHE_INPUT_MAP] = input_map
        self.save_cache()

    @cached_property
    def ziparchive(self):
        ziparchive = ZipArchive(self.archive_filename, self.box_name)

        self._check_and_populate_cache(ziparchive)

        return ziparchive

    def _check_and_populate_cache(self, ziparchive):
        def ensure(cache_key, value):
            try:
                if self.cache[cache_key] != value:
                    raise InvalidArchive(
                        'Cache disagrees with zip meta', self.archive_filename, cache_key)
            except KeyError:
                self.cache[cache_key] = value

        ensure(meta.META_VERSION, ziparchive.meta_version)
        ensure(CACHE_CONTENT_ID, ziparchive.content_id)
        ensure(meta.KIND, ziparchive.kind)
        ensure(meta.FREEZE_TIME, ziparchive.timestamp_str)
        ensure(meta.INPUTS, ziparchive.meta[meta.INPUTS])

        # need not match
        self.cache.setdefault(CACHE_INPUT_MAP, ziparchive.input_map)

    @property
    def is_valid(self):
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
        workspace.meta = self.ziparchive.meta
        workspace.input_map = self.input_map


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
