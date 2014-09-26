from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import hashlib
from uuid import uuid1


def uuid():
    '''
    Return a new universally unique id as a unicode string consisting of
    only ASCII characters.

    The returned string can be expected to be highly unlikely to be generated
    twice.

    There is no format restriction on the returned strings, so this algorithm
    can change in the future.
    The returned string can not be expected to follow the format of RFC 4122.

    One important property needs to be preserved when the algorithm changes:
    The uuids returned by the new algorithm should be highly unlikely to ever
    collide with previously generated uuids.

    E.g, it can be achieved by returning progressively longer strings with
    each change, or adding a constant (but algorithm specific) prefix to all
    uuids generated.
    '''
    return ''.__class__(hashlib.md5(uuid1().hex.encode('utf-8')).hexdigest())
