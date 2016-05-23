'''
Keys for accessing fields in .BEAD_META structures

.BEAD_META files are persistent python dictionaries,
with the following minimum structure:

{
    meta_version: ...,        # uuid
    hash_function_uuid: ...,  # uuid
    inputs: {
        'nick1' : {
            bead_uuid: ...,           # uuid
            hash_function_uuid: ...,  # uuid
            content_hash: ...,
            freeze_time: ...,
        },
        'nick2' : {
            bead_uuid: ...,           # uuid
            hash_function_uuid: ...,  # uuid
            content_hash: ...,
            freeze_time: ...,
        },
        ...
    },
    bead_uuid: ...,    # uuid
    freeze_time: ...,  # only archives - naive ordering
    freeze_name: ...,  # only archives, bead name for bootstrapping
}
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


from collections import namedtuple


# Metadata versions determine how the data should be interpreted.
# Having this version in the metadata potentially enables interoperability
# and backwards compatibility of BEADs.
# If the metadata ever needs to be changed/upgraded we still
# want existing BEADs to remain connected and alive.

META_VERSION = 'meta_version'

# Defines the hash function used in hashing file contents for the checksums file
# and further hashing in to get the BEAD's CONTENT_HASH
HASH_FUNCTION_UUID = 'hash_function_uuid'

BEAD_UUID = 'bead_uuid'

INPUTS = 'inputs'

INPUT_BEAD_UUID          = BEAD_UUID
INPUT_HASH_FUNCTION_UUID = HASH_FUNCTION_UUID
INPUT_CONTENT_HASH       = 'content_hash'
INPUT_FREEZE_TIME        = 'freeze_time'


InputSpec = namedtuple('InputSpec', 'name bead_uuid hash_function_uuid content_hash timestamp')


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
            spec[INPUT_HASH_FUNCTION_UUID],
            spec[INPUT_CONTENT_HASH],
            spec[INPUT_FREEZE_TIME])


# Archive meta:
FREEZE_TIME = 'freeze_time'
FREEZE_NAME = 'freeze_name'
