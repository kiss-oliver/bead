from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import io
import os
import zipfile

from .. import tech
from . import layouts
from . import metakey

# technology modules
timestamp = tech.timestamp
securehash = tech.securehash
persistence = tech.persistence
path = tech.fs


class Archive(object):

    def __init__(self, filename):
        self.zipfile = zipfile.ZipFile(filename)

    # with protocol - context manager
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.zipfile.close()

    # -
    @property
    def is_valid(self):
        # TODO
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
        valid = all((
            metakey.PACKAGE in self.meta,
            metakey.PACKAGE_TIMESTAMP in self.meta,
            metakey.INPUTS in self.meta,
            metakey.DEFAULT_NAME in self.meta,
        ))

        if valid:
            now = timestamp.time_from_timestamp(timestamp.timestamp())
            pkgtime = timestamp.time_from_timestamp(
                self.meta[metakey.PACKAGE_TIMESTAMP]
            )
            valid = pkgtime < now

        return valid

    @property
    def version(self):
        zipinfo = self.zipfile.getinfo(layouts.Archive.CHECKSUMS)
        with self.zipfile.open(zipinfo) as f:
            return securehash.file(f, zipinfo.file_size)

    @property
    def uuid(self):
        return self.meta[metakey.PACKAGE]

    @property
    def meta(self):
        with self.zipfile.open(layouts.Archive.PKGMETA) as f:
            return persistence.load(io.TextIOWrapper(f))

    # -
    def extract_file(self, zip_path, destination):
        '''Extract zip_path from zipfile to destination'''

        assert not os.path.exists(destination)

        with path.temp_dir(destination.parent) as unzip_dir:
            self.zipfile.extract(zip_path, unzip_dir)
            os.rename(unzip_dir / zip_path, destination)

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

    def extract_code_to(self, destination):
        self.extract_dir(layouts.Archive.CODE, destination)

    def extract_data_to(self, destination):
        self.extract_dir(layouts.Archive.DATA, destination)
