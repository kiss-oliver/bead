'''
Keys for accessing fields in .pkgmeta structures

.pkgmeta files are persistent python dictionaries,
with the following minimum structure:

{
    inputs: {
        'mount point1' : {
            package uuid: ...,
            version uuid: ...,
            file name: ...,
            mounted: true | false,
        },
        'mount point2' : {
            package uuid: ...,
            version uuid: ...,
            file name: ...,
            mounted: true | false,
        },
        ...
    },
    package uuid: ...,
    timestamp: ...,        # only archives - naive ordering
    unofficial name: ...,  # only archives, package name for bootstrapping
}
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


KEY_PACKAGE = 'package uuid'

KEY_INPUTS = 'inputs'

KEY_INPUT_PACKAGE = 'package uuid'
KEY_INPUT_VERSION = 'version uuid'
KEY_INPUT_FILENAME = 'file name'
KEY_INPUT_MOUNTED = 'mounted'

# TODO: ***FUTURE***
# KEY_INPUT_CHANNEL = 'upgrade channel uuid'

# Archive meta:
KEY_PACKAGE_TIMESTAMP = 'timestamp'
# TODO: decide if KEY_UNOFFICIAL_NAME needed
KEY_UNOFFICIAL_NAME = 'unofficial name'

# Workspace meta:
KEY_REPO_ROOT = 'repo'
