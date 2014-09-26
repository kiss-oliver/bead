'''
Filesystem layout of packages
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import zipfile

from . import layouts
from . import metakey
from .. import tech

# technology modules
persistence = tech.persistence
securehash = tech.securehash
fs = tech.fs


class Workspace(object):

    def __init__(self, directory='.'):
        self.directory = fs.Path(os.path.abspath(directory))

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

    @property
    def flat_repo(self):
        return fs.read_file(self.directory / layouts.Workspace.REPO)

    @flat_repo.setter
    def flat_repo(self, directory):
        fs.write_file(self.directory / layouts.Workspace.REPO, directory)

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
            metakey.PACKAGE: tech.identifier.uuid(),
            metakey.INPUTS: {},
        }
        fs.write_file(
            dir / layouts.Workspace.PKGMETA,
            persistence.to_string(pkgmeta)
        )
        self.flat_repo = '..'

        assert self.is_valid

    def create_directories(self):
        dir = self.directory
        fs.ensure_directory(dir)
        fs.ensure_directory(dir / layouts.Workspace.INPUT)
        fs.make_readonly(dir / layouts.Workspace.INPUT)
        fs.ensure_directory(dir / layouts.Workspace.OUTPUT)
        fs.ensure_directory(dir / layouts.Workspace.TEMP)
        fs.ensure_directory(dir / layouts.Workspace.META)

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
        return nick in self.meta[metakey.INPUTS]

    def is_mounted(self, nick):
        try:
            return self.meta[metakey.INPUTS][nick][metakey.INPUT_MOUNTED]
        except KeyError:
            return False

    def add_input(self, nick, uuid, version):
        m = self.meta
        m[metakey.INPUTS][nick] = {
            metakey.INPUT_PACKAGE: uuid,
            metakey.INPUT_VERSION: version,
            metakey.INPUT_MOUNTED: False
        }
        self.meta = m

    def delete_input(self, nick):
        # XXX should be merged into unmount?
        assert self.has_input(nick)
        if self.is_mounted(nick):
            self.unmount(nick)
        m = self.meta
        del m[metakey.INPUTS][nick]
        self.meta = m

    def mark_input_mounted(self, nick, mounted):
        m = self.meta
        m[metakey.INPUTS][nick][metakey.INPUT_MOUNTED] = mounted
        self.meta = m

    def mount(self, nick, archive):
        input_dir = self.directory / layouts.Workspace.INPUT
        fs.make_writable(input_dir)
        try:
            self.add_input(nick, archive.uuid, archive.version)
            mount_dir = input_dir / nick
            archive.extract_dir(layouts.Archive.DATA, mount_dir)
            for f in fs.all_subpaths(mount_dir):
                fs.make_readonly(f)
            self.mark_input_mounted(nick, True)
        finally:
            fs.make_readonly(input_dir)

    def unmount(self, nick):
        assert self.has_input(nick)
        input_dir = self.directory / layouts.Workspace.INPUT
        fs.make_writable(input_dir)
        try:
            fs.rmtree(input_dir / nick)
            self.mark_input_mounted(nick, False)
        finally:
            fs.make_readonly(input_dir)


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
            metakey.PACKAGE: wsmeta[metakey.PACKAGE],
            metakey.PACKAGE_TIMESTAMP: timestamp,
            metakey.INPUTS: {
                nick: {
                    metakey.INPUT_PACKAGE: spec[metakey.INPUT_PACKAGE],
                    metakey.INPUT_VERSION: spec[metakey.INPUT_VERSION],
                }
                for nick, spec in wsmeta[metakey.INPUTS].items()
            },
            metakey.DEFAULT_NAME: workspace.package_name,
        }

        self.add_string_content(
            layouts.Archive.PKGMETA,
            persistence.to_string(pkgmeta)
        )
        self.add_string_content(
            layouts.Archive.CHECKSUMS,
            persistence.to_string(self.hashes)
        )
