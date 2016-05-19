from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


ENV       = 'directory that defines e.g. the boxes'
WORKSPACE = 'workspace directory'
BEAD_REF  = '''
    bead to load data from
    - either an archive file name or a bead name
'''
INPUT_NICK = (
    'name of input,'
    + ' its workspace relative location is "input/%(metavar)s"')
BOX = 'Name of box to store bead'
