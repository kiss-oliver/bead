from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import hashlib

READ_BLOCK_SIZE = 1024 ** 2

# hashes are created from {length of content}:content;
# similarity to http://cr.yp.to/proto/netstrings.txt are not accidental:
# length is hashed with content AND there is a known suffix


def file(file, file_size):
    '''Read file and return sha512 hash for its content.

    Closes the file.
    Can process BIG files.
    '''

    hash = hashlib.sha512()
    hash.update('{}:'.format(file_size).encode('ascii'))
    with file:
        while True:
            block = file.read(READ_BLOCK_SIZE)
            if not block:
                break
            hash.update(block)
    hash.update(b';')
    return ''.__class__(hash.hexdigest())


def bytes(bytes):
    '''Return sha512 hash for bytes.
    '''
    hash = hashlib.sha512()
    hash.update('{}:'.format(len(bytes)).encode('ascii'))
    hash.update(bytes)
    hash.update(b';')
    return ''.__class__(hash.hexdigest())
