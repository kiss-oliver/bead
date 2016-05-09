from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


WORKSPACE = 'workspace directory'
BEAD_LOAD = '''
    bead to load data from
    - either an archive file name
    or a BEAD NAME + selection criteria (e.g. by time)
'''
INPUT_NICK = (
    'name of input,'
    + ' its workspace relative location is "input/%(metavar)s"')
