from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import zipfile

from .. import path
from ..path import temp_dir
from .. import securehash
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
