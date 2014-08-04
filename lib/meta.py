'''
Keys for accessing fields in .pkgmeta structures

.pkgmeta files are persistent python dictionaries,
with the following minimum structure:

{
    inputs: {
        'mount point1' : {
            package uuid: ...,
            version uuid: ...
        },
        'mount point2' : {
            package uuid: ...,
            version uuid: ...
        },
        ...
    },
    package uuid: ...,
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

# TODO: ***FUTURE***
# KEY_INPUT_CHANNEL = 'upgrade channel uuid'

KEY_PACKAGE_TIMESTAMP = 'timestamp'
