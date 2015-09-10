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
from . import meta
from .. import tech

# technology modules
persistence = tech.persistence
securehash = tech.securehash
fs = tech.fs


class AbstractWorkspace(object):

    # directory of workspace - subclasses need to specify it
    directory = None

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
    def meta_path(self):
        return self.directory / layouts.Workspace.PKGMETA

    @property
    def meta(self):
        with open(self.meta_path) as f:
            return persistence.load(f)

    @meta.setter
    def meta(self, meta):
        with open(self.meta_path, 'wt') as f:
            return persistence.dump(meta, f)

    @property
    def uuid(self):
        return self.meta[meta.PACKAGE]

    @property
    def inputs(self):
        return meta.parse_inputs(self.meta)

    def get_input(self, name):
        for input in self.inputs:
            if name == input.name:
                return input

    def create(self, uuid):
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
            meta.PACKAGE: uuid,
            meta.INPUTS: {},
        }
        fs.write_file(
            dir / layouts.Workspace.PKGMETA,
            persistence.dumps(pkgmeta)
        )

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

    def has_input(self, input_nick):
        '''
        Is there an input defined for input_nick?

        NOTE: it is not necessarily mounted!
        '''
        return input_nick in self.meta[meta.INPUTS]

    def is_mounted(self, input_nick):
        return os.path.isdir(
            self.directory / layouts.Workspace.INPUT / input_nick)

    def add_input(self, input_nick, uuid, version):
        m = self.meta
        m[meta.INPUTS][input_nick] = {
            meta.INPUT_PACKAGE: uuid,
            meta.INPUT_VERSION: version,
        }
        self.meta = m

    def delete_input(self, input_nick):
        assert self.has_input(input_nick)
        if self.is_mounted(input_nick):
            self.unmount(input_nick)
        m = self.meta
        del m[meta.INPUTS][input_nick]
        self.meta = m

    def mount(self, input_nick, package):
        '''
        Make output data files in package available under input directory
        '''
        input_dir = self.directory / layouts.Workspace.INPUT
        fs.make_writable(input_dir)
        try:
            self.add_input(input_nick, package.uuid, package.version)
            mount_dir = input_dir / input_nick
            package.unpack_data_to(mount_dir)
            for f in fs.all_subpaths(mount_dir):
                fs.make_readonly(f)
        finally:
            fs.make_readonly(input_dir)

    def unmount(self, input_nick):
        '''
        Remove files for given input
        '''
        assert self.has_input(input_nick)
        input_dir = self.directory / layouts.Workspace.INPUT
        fs.make_writable(input_dir)
        try:
            fs.rmtree(input_dir / input_nick)
        finally:
            fs.make_readonly(input_dir)

    def __repr__(self):
        # argh prints default value as repr of the value
        return self.directory


class Workspace(AbstractWorkspace):

    def __init__(self, directory):
        super(Workspace, self).__init__()
        self.directory = fs.Path(os.path.abspath(directory))


class CurrentDirWorkspace(AbstractWorkspace):

    @property
    def directory(self):
        return fs.Path(os.path.abspath(os.getcwd()))


class _ZipCreator(object):
    # FIXME: add zip comment with pointers to this software

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
        pkgmeta = {
            meta.PACKAGE: workspace.uuid,
            meta.PACKAGE_TIMESTAMP: timestamp,
            meta.INPUTS: {
                input.name: {
                    meta.INPUT_PACKAGE: input.package,
                    meta.INPUT_VERSION: input.version,
                }
                for input in workspace.inputs
            },
            meta.DEFAULT_NAME: workspace.package_name,
        }

        self.add_string_content(
            layouts.Archive.PKGMETA,
            persistence.dumps(pkgmeta)
        )
        self.add_string_content(
            layouts.Archive.CHECKSUMS,
            persistence.dumps(self.hashes)
        )
