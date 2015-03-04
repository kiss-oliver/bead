'''
layout of packages
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from .. import tech

Path = tech.fs.Path


class Archive:

    DATA = Path('data')
    META = Path('meta')
    CODE = META / 'code'

    PKGMETA = META / 'pkgmeta'
    CHECKSUMS = META / 'checksums'


class Workspace:

    INPUT = Path('input')
    OUTPUT = Path('output')
    TEMP = Path('temp')
    META = Path('.santa')

    PKGMETA = META / 'package'
    REPO = META / 'repo'
