'''
layout of packages
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..path import Path


class Archive:

    DATA = Path('data')
    META = Path('meta')
    CODE = META / 'code'

    META_PKGMETA = META / 'pkgmeta'
    META_CHECKSUMS = META / 'checksums'


class Workspace:

    INPUT = Path('input')
    OUTPUT = Path('output')
    TEMP = Path('temp')
    PKGMETA = '.pkgmeta'
