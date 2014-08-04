'''
Archive layout of packages
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..path import Path


DATA_PATH = Path('data')
CODE_PATH = Path('code')
META_PATH = Path('meta')

META_PKGMETA = META_PATH / 'pkgmeta'
META_CHECKSUMS = META_PATH / 'checksums'


def is_valid(zipfile):
    # TODO
    return True
