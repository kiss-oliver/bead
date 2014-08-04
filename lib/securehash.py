from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import hashlib

READ_BLOCK_SIZE = 1024 ** 2


# FIXME: hash should be created from (length of content, content)
# in practice this means something like hashing netstrings
# http://cr.yp.to/proto/netstrings.txt
#

def file(file):
    '''Read file and return sha512 hash for its content.

    Closes the file.
    Can process BIG files.
    '''

    hash = hashlib.sha512()
    with file:
        while True:
            block = file.read(READ_BLOCK_SIZE)
            if not block:
                break
            hash.update(block)
    return hash


def bytes(bytes):
    '''Return sha512 hash for bytes.
    '''
    return hashlib.sha512(bytes)
