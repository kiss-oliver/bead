from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import tempfile
import zipfile

from .. import path
from ..path import Path, temp_dir
from .. import securehash
from .workspace import Workspace
from .. import persistence
from . import layouts


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
        return True

    @property
    def version(self):
        with self.zipfile.open(layouts.Archive.META_CHECKSUMS) as f:
            return securehash.file(f)

    # -
    def extract_file(self, zip_path, destination):
        '''Extract zip_path from zipfile to destination'''

        assert not os.path.exists(destination)

        with temp_dir(path.parent(destination)) as unzip_dir:
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
            with temp_dir(path.parent(destination)) as unzip_dir:
                self.zipfile.extractall(unzip_dir, filelist)
                os.rename(unzip_dir / zip_dir, destination)
        else:
            # FIXME: untested
            path.ensure_directory(destination)


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

    def add_string_content(self, zip_path, string):
        bytes = string.encode('utf-8')
        self.zipfile.writestr(zip_path, bytes)
        self.add_hash(zip_path, securehash.bytes(bytes))

    def create(self, zip_file_name, source_directory):
        source_path = Path(source_directory)
        assert Workspace(source_path).is_valid
        try:
            self.zipfile = zipfile.ZipFile(
                zip_file_name,
                mode='w',
                compression=zipfile.ZIP_DEFLATED,
                allowZip64=True,
            )
            self.create_from(source_path)
            self.zipfile.close()
            assert Archive(zip_file_name).is_valid
        finally:
            self.zipfile = None

    def add_code(self, source_directory):
        def is_code(f):
            return f not in {
                layouts.Workspace.INPUT,
                layouts.Workspace.OUTPUT,
                layouts.Workspace.PKGMETA,
                layouts.Workspace.TEMP
            }

        for f in sorted(os.listdir(source_directory)):
            if is_code(f):
                self.add_path(
                    source_directory / f,
                    layouts.Archive.CODE / f
                )

    def add_data(self, source_directory):
        self.add_directory(
            source_directory / layouts.Workspace.OUTPUT,
            layouts.Archive.DATA
        )

    def add_meta(self, source_directory):
        # FIXME: add_meta is dummy, to be completed, when Archive is defined
        pkgmeta = persistence.to_string({'TODO': 'FIXME'})
        self.add_string_content(layouts.Archive.META_PKGMETA, pkgmeta)
        self.add_string_content(layouts.Archive.META_CHECKSUMS, self.checksums)

    def create_from(self, source_directory):
        assert self.zipfile

        self.add_data(source_directory)
        self.add_code(source_directory)
        self.add_meta(source_directory)


def create(source_directory):
    source_path = Path(source_directory)
    fd, tempname = tempfile.mkstemp(
        dir=source_path / layouts.Workspace.TEMP, prefix='', suffix='.pkg'
    )
    os.close(fd)
    os.remove(tempname)
    ZipCreator().create(tempname, source_directory)
    return tempname
