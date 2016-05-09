'''
Keys for accessing fields in .BEAD_META structures

.BEAD_META files are persistent python dictionaries,
with the following minimum structure:

{
    inputs: {
        'nick1' : {
            bead_uuid: ...,
            content_hash: ...,
            freeze_time: ...,
        },
        'nick2' : {
            bead_uuid: ...,
            content_hash: ...,
            freeze_time: ...,
        },
        ...
    },
    bead_uuid: ...,
    timestamp: ...,     # only archives - naive ordering
    default name: ...,  # only archives, package name for bootstrapping
}
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


from collections import namedtuple


BEAD_UUID = 'bead_uuid'

INPUTS = 'inputs'

INPUT_BEAD_UUID    = 'bead_uuid'
INPUT_CONTENT_HASH = 'content_hash'
INPUT_FREEZE_TIME  = 'freeze_time'

# FIXME: rename `version` to `content-hash`
InputSpec = namedtuple('InputSpec', 'name package version timestamp')


def parse_inputs(meta):
    '''
    Parse and yield input specification from meta as records.
    '''
    inputs = meta[INPUTS]
    for name in inputs:
        spec = inputs[name]
        yield InputSpec(
            name,
            spec[INPUT_BEAD_UUID],
            spec[INPUT_CONTENT_HASH],
            spec[INPUT_FREEZE_TIME])


# Archive meta:
FREEZE_TIME = 'freeze_time'
FREEZE_NAME = 'freeze_name'
