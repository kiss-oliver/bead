from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import io
import os
import stat
import contextlib
import shutil
import tempfile


class Path(''.__class__):

    def __div__(self, other):
        return self.__class__(os.path.join(self, other))

    __truediv__ = __div__


def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

    assert os.path.isdir(path)


def write_file(path, content):
    if isinstance(content, bytes):
        f = open(path, 'wb')
    else:
        f = io.open(path, 'wt', encoding='utf-8')

    with f:
        f.write(content)


def read_file(path):
    with io.open(path, 'rt', encoding='utf-8') as f:
        return f.read()


@contextlib.contextmanager
def temp_dir(dir='.'):
    ensure_directory(dir)

    temp_dir = tempfile.mkdtemp(dir=dir)
    try:
        yield Path(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def make_readonly(path):
    mode = os.stat(path)[stat.ST_MODE]
    os.chmod(path, mode & ~stat.S_IWRITE)


def make_writable(path):
    mode = os.stat(path)[stat.ST_MODE]
    os.chmod(path, mode | stat.S_IWRITE)


def all_subpaths(dir):
    for root, dirs, files in os.walk(dir):
        root = Path(root)
        yield root
        for file in files:
            yield root / file


def rmtree(root, *args, **kwargs):
    for path in all_subpaths(root):
        make_writable(path)
    shutil.rmtree(root, *args, **kwargs)
