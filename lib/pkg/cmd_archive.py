'''
Tool to create a data package archive from a directory
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import sys
import zipfile

from ..path import Path
from .. import meta
from . import pkg_zip
from . import pkg_dir
from .. import securehash


class ZipCreator(object):

    def __init__(self):
        self.hashes = {}
        self.zipfile = None

    def add_hash(self, path, hash):
        assert path not in self.hashes
        self.hashes[path] = hash

    @property
    def checksums(self):
        return ''.join(
            '{} {}\n'.format(hash, name)
            for name, hash in sorted(self.hashes.items())
        )

    def add_file(self, path, zip_path):
        self.zipfile.write(path, zip_path)
        self.add_hash(zip_path, securehash.file(open(path, 'rb')))

    def add_path(self, path, zip_path):
        if os.path.islink(path):
            raise ValueError(
                'workspace contains a link: {}'.format(path)
            )
        elif os.path.isdir(path):
            self.add_directory(path, zip_path)
        elif os.path.isfile(path):
            self.add_file(path, zip_path)

    def add_directory(self, path, zip_path):
        for f in os.listdir(path):
            self.add_path(path / f, zip_path / f)

    def add_content(self, zip_path, bytes):
        self.zipfile.writestr(zip_path, bytes)
        self.add_hash(zip_path, securehash.bytes(bytes))

    def create(self, zip_file_name, source_directory):
        source_path = Path(source_directory)
        assert pkg_dir.is_valid(source_path)
        try:
            self.zipfile = zipfile.ZipFile(
                zip_file_name,
                mode='w',
                compression=zipfile.ZIP_DEFLATED,
                allowZip64=True,
            )
            self.create_from(source_path)
            self.zipfile.close()
        finally:
            self.zipfile = None

    def add_code(self, source_directory):
        def is_code(f):
            return f not in {
                pkg_dir.INPUT,
                pkg_dir.OUTPUT,
                pkg_dir.PKGMETA,
                pkg_dir.TEMP
            }

        for f in sorted(os.listdir(source_directory)):
            if is_code(f):
                self.add_path(
                    source_directory / f,
                    pkg_zip.CODE_PATH / f
                )

    def add_data(self, source_directory):
        self.add_directory(
            source_directory / pkg_dir.OUTPUT,
            pkg_zip.DATA_PATH
        )

    def add_meta(self, source_directory):
        # FIXME: add_meta is dummy, to be completed, when pkg_zip is defined
        pkgmeta = meta.to_string({'TODO': 'FIXME'})
        self.add_content(pkg_zip.META_PKGMETA, pkgmeta)
        self.add_content(pkg_zip.META_CHECKSUMS, self.checksums)

    def create_from(self, source_directory):
        assert self.zipfile

        self.add_data(source_directory)
        self.add_code(source_directory)
        self.add_meta(source_directory)

        assert pkg_zip.is_valid(self.zipfile)


def create(zip_file_name, source_directory):
    ZipCreator().create(zip_file_name, source_directory)


def main():
    zip_file_name, source_directory = sys.argv[1:]
    create(zip_file_name, source_directory)


if __name__ == '__main__':
    main()
