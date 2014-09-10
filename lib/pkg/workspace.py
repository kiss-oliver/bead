'''
Filesystem layout of packages
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import zipfile

from ..path import Path, ensure_directory, all_subpaths, make_readonly
from .. import persistence
from .. import securehash
from ..identifier import uuid
from . import layouts
from . import meta


class Workspace(object):

    def __init__(self, directory='.'):
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

    @property
    def meta(self):
        with open(self.directory / layouts.Workspace.PKGMETA) as f:
            return persistence.from_stream(f)

    @meta.setter
    def meta(self, meta):
        with open(self.directory / layouts.Workspace.PKGMETA, 'wt') as f:
            return persistence.to_stream(meta, f)

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

        pkgmeta = {
            meta.KEY_PACKAGE: uuid(),
            meta.KEY_INPUTS: {},
        }
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

    def pack(self, zipfilename, timestamp):
        '''
        Create archive from workspace.
        '''

        _ZipCreator().create(zipfilename, self, timestamp)

    def has_input(self, nick):
        '''Is there an input defined for nick?

        NOTE: it is not necessarily mounted!
        '''
        return nick in self.meta[meta.KEY_INPUTS]

    def is_mounted(self, nick):
        try:
            return self.meta[meta.KEY_INPUTS][nick][meta.KEY_INPUT_MOUNTED]
        except KeyError:
            return False

    def add_input(self, nick, uuid, version):
        m = self.meta
        m[meta.KEY_INPUTS][nick] = {
            meta.KEY_INPUT_PACKAGE: uuid,
            meta.KEY_INPUT_VERSION: version,
            meta.KEY_INPUT_MOUNTED: False
        }
        self.meta = m

    def mark_input_mounted(self, nick, mounted):
        m = self.meta
        m[meta.KEY_INPUTS][nick][meta.KEY_INPUT_MOUNTED] = mounted
        self.meta = m

    def mount(self, nick, archive):
        self.add_input(nick, archive.uuid, archive.version)
        mount_dir = self.directory / layouts.Workspace.INPUT / nick
        archive.extract_dir(layouts.Archive.DATA, mount_dir)
        for f in all_subpaths(mount_dir):
            make_readonly(f)
        self.mark_input_mounted(nick, True)


class _ZipCreator(object):

    def __init__(self):
        self.hashes = {}
        self.zipfile = None

    def add_hash(self, path, hash):
        assert path not in self.hashes
        self.hashes[path] = hash

    def add_file(self, path, zip_path):
        self.zipfile.write(path, zip_path)
        self.add_hash(
            zip_path,
            securehash.file(open(path, 'rb'), os.path.getsize(path))
        )

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

    def create(self, zip_file_name, workspace, timestamp):
        assert workspace.is_valid
        try:
            with zipfile.ZipFile(
                zip_file_name,
                mode='w',
                compression=zipfile.ZIP_DEFLATED,
                allowZip64=True,
            ) as self.zipfile:
                self.add_data(workspace)
                self.add_code(workspace)
                self.add_meta(workspace, timestamp)
        finally:
            self.zipfile = None

    def add_code(self, workspace):
        source_directory = workspace.directory

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

    def add_data(self, workspace):
        self.add_directory(
            workspace.directory / layouts.Workspace.OUTPUT,
            layouts.Archive.DATA
        )

    def add_meta(self, workspace, timestamp):
        wsmeta = workspace.meta
        pkgmeta = {
            meta.KEY_PACKAGE: wsmeta[meta.KEY_PACKAGE],
            meta.KEY_PACKAGE_TIMESTAMP: timestamp,
            meta.KEY_INPUTS: {},
            meta.KEY_DEFAULT_NAME: workspace.package_name,
        }
        # TODO: add INPUTS to pkgmeta

        self.add_string_content(
            layouts.Archive.PKGMETA,
            persistence.to_string(pkgmeta)
        )
        self.add_string_content(
            layouts.Archive.CHECKSUMS,
            persistence.to_string(self.hashes)
        )
