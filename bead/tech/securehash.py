'''
I am providing the content hash functions.
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import hashlib

READ_BLOCK_SIZE = 1024 ** 2

# hashes are created from {length of content}:content;
# similarity to http://cr.yp.to/proto/netstrings.txt are not accidental:
# length is hashed with content AND there is a known suffix


def _add_prefix(hash, size):
    hash.update('{}:'.format(size).encode('ascii'))


def _add_suffix(hash, size):
    hash.update(';{}'.format(size).encode('ascii'))


def _file(file, file_size):
    '''
    Read file and return sha512 hash for its content.

    Closes the file.
    Can process BIG files.
    '''

    hash = hashlib.sha512()
    _add_prefix(hash, file_size)

    bytes_read = 0

    with file:
        while True:
            block = file.read(READ_BLOCK_SIZE)
            if not block:
                break
            bytes_read += len(block)
            hash.update(block)

    assert bytes_read == file_size

    _add_suffix(hash, file_size)
    return ''.__class__(hash.hexdigest())


def _bytes(bytes):
    '''
    Return sha512 hash for bytes.
    '''
    hash = hashlib.sha512()
    _add_prefix(hash, len(bytes))
    hash.update(bytes)
    _add_suffix(hash, len(bytes))
    return ''.__class__(hash.hexdigest())


class Hash_sha512_sbs:
    name = 'sha512(size:bytes;size)'

    def bytes(self, bytes):
        return _bytes(bytes)

    def file(self, file, file_size):
        return _file(file, file_size)


# UUID[s] generated with `uuidgen -t`
HASHES = {
    'd4bb4e72-20f1-11e6-8b37-180373c6afa1': Hash_sha512_sbs,
}


# FIXME: securehash.get_hash_function is a misnomer as it returns an object with two functions
def get_hash_function(hash_function_uuid):
    hash_class = HASHES.get(hash_function_uuid)
    if hash_class:
        return hash_class()
