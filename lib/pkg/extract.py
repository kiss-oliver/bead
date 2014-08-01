from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import contextlib
import os
import shutil
import tempfile

from .. import path
from ..path import Path


@contextlib.contextmanager
def temp_dir(parent):
    path.ensure_directory(parent)

    temp_dir = tempfile.mkdtemp(dir=parent)
    try:
        yield Path(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def extract_file(zipfile, zip_path, destination):
    '''Extract zip_path from zipfile to destination'''

    assert not os.path.exists(destination)

    with temp_dir(path.parent(destination)) as unzip_dir:
        zipfile.extract(zip_path, unzip_dir)
        os.rename(unzip_dir / zip_path, destination)


def extract_dir(zipfile, zip_dir, destination):
    '''
    Extract all files from zipfile under zip_dir to destination.
    '''

    assert not os.path.exists(destination)

    zip_dir_prefix = zip_dir + '/'
    filelist = [
        name
        for name in zipfile.namelist()
        if name.startswith(zip_dir_prefix)
    ]

    with temp_dir(path.parent(destination)) as unzip_dir:
        zipfile.extractall(unzip_dir, filelist)
        os.rename(unzip_dir / zip_dir, destination)


# FIXME: replace manual tests with automated ones
def main():
    import zipfile
    z = zipfile.ZipFile('/ramdisk/x.zip')
    extract_file(z, 'meta/checksums.sha512', '/ramdisk/xchecksum/checksums')
    extract_dir(z, 'data', '/ramdisk/xdata')
    extract_dir(z, 'code', '/ramdisk/xcode/x')


if __name__ == '__main__':
    main()
