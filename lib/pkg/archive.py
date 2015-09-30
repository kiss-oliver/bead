from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from copy import deepcopy
import functools
import io
import os
import zipfile

from .package import Package
from .. import tech
from . import layouts
from . import meta

# technology modules
timestamp = tech.timestamp
securehash = tech.securehash
persistence = tech.persistence
path = tech.fs


class Archive(Package):

    def __init__(self, filename):
        self.archive_filename = filename
        self.zipfile = None
        self._meta = self._load_meta()

    def __zipfile_user(method):
        # method is called with the zipfile opened
        @functools.wraps(method)
        def f(self, *args, **kwargs):
            if self.zipfile:
                return method(self, *args, **kwargs)
            try:
                with zipfile.ZipFile(self.archive_filename) as self.zipfile:
                    return method(self, *args, **kwargs)
            finally:
                self.zipfile = None
        return f

    def export(self, exported_archive_path):
        '''
        I pack my content (everything!) as a zip-Archive to requested location.
        '''
        # FIXME: Implement Archive.export
        pass

    # -
    @property
    @__zipfile_user
    def is_valid(self):
        # FIXME verify checksums!
        '''
        verify, that
        - all files under code, data, meta are present in the checksums
          file and they match their checksums
          (can extra files be allowed in the archive?)
        - the pkgmeta file is valid
            - has package uuid
            - has timestamp
            - has unofficial package name
            - has inputs (even if empty)
        '''
        return all(self._checks())

    def _checks(self):
        yield meta.PACKAGE in self.meta
        yield meta.PACKAGE_TIMESTAMP in self.meta
        yield meta.INPUTS in self.meta
        yield meta.DEFAULT_NAME in self.meta
        # verify package creation time
        read_time = timestamp.time_from_timestamp
        now = read_time(timestamp.timestamp())
        pkgtime = read_time(self.meta[meta.PACKAGE_TIMESTAMP])
        yield pkgtime < now
        yield self._check_extra_files() is None
        yield self._check_checksums() is None

    @__zipfile_user
    def _check_extra_files(self):
        data_dir_prefix = layouts.Archive.DATA + '/'
        code_dir_prefix = layouts.Archive.CODE + '/'
        checksums = self.checksums
        # check that there are no extra files
        for name in self.zipfile.namelist():
            is_data = name.startswith(data_dir_prefix)
            is_code = name.startswith(code_dir_prefix)
            if is_data or is_code:
                if name not in checksums:
                    # unexpected extra file!
                    return name

    @__zipfile_user
    def _check_checksums(self):
        for name, hash in self.checksums.items():
            try:
                info = self.zipfile.getinfo(name)
            except KeyError:
                return name
            # verify checksums

    @property
    @__zipfile_user
    def checksums(self):
        with self.zipfile.open(layouts.Archive.CHECKSUMS) as f:
            return persistence.load(f)

    @property
    @__zipfile_user
    def version(self):
        zipinfo = self.zipfile.getinfo(layouts.Archive.CHECKSUMS)
        with self.zipfile.open(zipinfo) as f:
            return securehash.file(f, zipinfo.file_size)

    @property
    def uuid(self):
        return self._meta[meta.PACKAGE]

    @property
    def timestamp_str(self):
        return self._meta[meta.PACKAGE_TIMESTAMP]

    @property
    def meta(self):
        # create a copy, so that returned meta can be modified without causing
        # harm to this Archive instance
        return deepcopy(self._meta)

    # -
    @__zipfile_user
    def _load_meta(self):
        with self.zipfile.open(layouts.Archive.PKGMETA) as f:
            return persistence.load(io.TextIOWrapper(f))

    @__zipfile_user
    def extract_file(self, zip_path, destination):
        '''Extract zip_path from zipfile to destination'''

        assert not os.path.exists(destination)

        with path.temp_dir(destination.parent) as unzip_dir:
            self.zipfile.extract(zip_path, unzip_dir)
            os.rename(unzip_dir / zip_path, destination)

    @__zipfile_user
    def extract_dir(self, zip_dir, destination):
        '''
        Extract all files from zipfile under zip_dir to destination.
        '''

        assert not os.path.exists(destination)

        zip_dir_prefix = zip_dir + '/'
        filelist = [
            name
            for name in self.zipfile.namelist()
            if name.startswith(zip_dir_prefix)
        ]

        if filelist:
            with path.temp_dir(destination.parent) as unzip_dir:
                self.zipfile.extractall(unzip_dir, filelist)
                os.rename(unzip_dir / zip_dir, destination)
        else:
            path.ensure_directory(destination)

    def unpack_code_to(self, destination):
        self.extract_dir(layouts.Archive.CODE, destination)

    def unpack_data_to(self, destination):
        self.extract_dir(layouts.Archive.DATA, destination)

    def unpack_meta_to(self, workspace):
        workspace.meta = self.meta
