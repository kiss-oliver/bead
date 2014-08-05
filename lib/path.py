from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os


class Path(''.__class__):

    def __div__(self, other):
        return self.__class__(os.path.join(self, other))

    __truediv__ = __div__


def segments(path):
    '''List of non-empty path segments
    '''
    def segments(path):
        next_path, name = os.path.split(path)
        if next_path:
            if next_path != path:
                return segments(next_path) + [name]
            return [next_path, name]
        return [name]
    return [s for s in segments(os.path.realpath(path)) if s]


def contains(directory, file_name):
    '''Creating `file_name` would be in subtree of `directory`?
    '''
    directory_segments = segments(directory)
    file_name_segments = segments(file_name)
    return file_name_segments[:len(directory_segments)] == directory_segments


def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

    assert os.path.isdir(path)


def parent(path):
    return Path(os.path.normpath(Path(path) / '..'))


def write_file(path, content):
    if isinstance(content, bytes):
        f = open(path, 'wb')
    else:
        f = open(path, 'wt', encoding='utf-8')

    with f:
        f.write(content)
