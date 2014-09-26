'''
Keys for accessing fields in .pkgmeta structures

.pkgmeta files are persistent python dictionaries,
with the following minimum structure:

{
    inputs: {
        'mount point1' : {
            package uuid: ...,
            version uuid: ...,
            mounted: true | false,
        },
        'mount point2' : {
            package uuid: ...,
            version uuid: ...,
            mounted: true | false,
        },
        ...
    },
    package uuid: ...,
    timestamp: ...,     # only archives - naive ordering
    default name: ...,  # only archives, package name for bootstrapping
}
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


PACKAGE = 'package uuid'

INPUTS = 'inputs'

INPUT_PACKAGE = 'package uuid'
INPUT_VERSION = 'version uuid'
INPUT_MOUNTED = 'mounted'

# TODO: ***FUTURE***
# INPUT_CHANNEL = 'upgrade channel uuid'

# Archive meta:
PACKAGE_TIMESTAMP = 'timestamp'
DEFAULT_NAME = 'default name'
