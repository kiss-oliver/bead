'''
Filesystem layout of packages
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import tempfile
import zipfile

from ..path import Path, ensure_directory
from .. import persistence
from .. import securehash
from . import layouts


class Workspace(object):

    def __init__(self, directory):
        self.directory = Path(os.path.abspath(directory))

    @property
    def is_valid(self):
        dir = self.directory
        return all(
            (
                os.path.isdir(dir / layouts.Workspace.INPUT),
                os.path.isdir(dir / layouts.Workspace.OUTPUT),
                os.path.isdir(dir / layouts.Workspace.TEMP),
                os.path.isfile(dir / layouts.Workspace.PKGMETA),
            )
        )

    def create(self):
        '''
        Set up an empty project structure.

        Works with either an empty directory or a directory to be created.
        '''
        dir = self.directory
        try:
            assert os.listdir(dir) == []
        except OSError:
            pass

        self.create_directories()

        pkgmeta = {}  # TODO
        with open(dir / layouts.Workspace.PKGMETA, 'w') as f:
            persistence.to_stream(pkgmeta, f)

        assert self.is_valid

    def create_directories(self):
        dir = self.directory
        ensure_directory(dir)
        ensure_directory(dir / layouts.Workspace.INPUT)
        ensure_directory(dir / layouts.Workspace.OUTPUT)
        ensure_directory(dir / layouts.Workspace.TEMP)

    @property
    def package_name(self):
        return os.path.basename(self.directory)

    def pack(self):
        '''
        Create archive from workspace into the temp directory.

        returns the path to the created archive.
        '''
        source_path = self.directory
        fd, tempname = tempfile.mkstemp(
            dir=source_path / layouts.Workspace.TEMP, prefix='', suffix='.pkg'
        )
        os.close(fd)
        os.remove(tempname)
        _ZipCreator().create(tempname, self)
        return tempname


class _ZipCreator(object):

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

    def create(self, zip_file_name, workspace):
        assert workspace.is_valid
        source_path = workspace.directory
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
