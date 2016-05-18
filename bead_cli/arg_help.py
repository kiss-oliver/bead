from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


ENV       = 'directory that has file[s] that defines e.g. user defined repositories'
WORKSPACE = 'workspace directory'
BEAD_REF  = '''
    bead to load data from
    - either an archive file name
    or a BEAD NAME + selection criteria (e.g. by time)
'''
INPUT_NICK = (
    'name of input,'
    + ' its workspace relative location is "input/%(metavar)s"')
REPOSITORY = 'Name of repository to store bead'
