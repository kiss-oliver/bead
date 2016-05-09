'''
Keys for accessing fields in .pkgmeta structures

.pkgmeta files are persistent python dictionaries,
with the following minimum structure:

{
    inputs: {
        'nick1' : {
            bead_uuid: ...,
            version hash: ...,
            version time: ...,
        },
        'nick2' : {
            bead_uuid: ...,
            version hash: ...,
            version time: ...,
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


PACKAGE = 'bead_uuid'

INPUTS = 'inputs'

# FIXME: new constant names: INPUT_BEAD_ID, INPUT_CONTENT_HASH, INPUT_FREEZE_TIME
INPUT_PACKAGE = 'bead_uuid'
# FIXME: rename `version` to `content-hash`
INPUT_VERSION = 'version hash'
INPUT_TIME = 'version time'

InputSpec = namedtuple('InputSpec', 'name package version timestamp')


def parse_inputs(meta):
    '''
    Parse and yield input specification from meta as records.
    '''
    inputs = meta[INPUTS]
    for name in inputs:
        spec = inputs[name]
        yield InputSpec(name, spec[INPUT_PACKAGE], spec[INPUT_VERSION], spec[INPUT_TIME])


# Archive meta:
# FIXME: new constant names: FREEZE_TIME, FREEZE_NAME
PACKAGE_TIMESTAMP = 'timestamp'
DEFAULT_NAME = 'default name'
