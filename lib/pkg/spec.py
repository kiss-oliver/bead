from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import re
from collections import namedtuple


# TODO: parse and return 'offset' - "offset to last matching version"
PackageSpec = namedtuple('PackageSpec', 'peer name version offset')


_parse = re.compile(
    r'''
    ^
    # peer is optional
    (
        (?P<peer>[^:@]*)
        :
    )?

    # name is mandatory
    (?P<name>[^:@]+)

    # version is optional
    (
        @
        (?P<version>[^-:@]+)
        (-(?P<offset>[0-9]+))?
    )?
    $
    ''', re.VERBOSE).match


def parse(string):
    '''
    Parse a string based package specification.

    Parts of the returned package specification:
    - peer (optional, defaults to self = empty string)
    - name (mandatory)
    - version (optional, defaults to None)
    '''
    match = _parse(string)
    if match:
        m = match.groupdict()
        offset = int(m['offset'] or '0')
        return PackageSpec(m['peer'] or '', m['name'], m['version'], offset)
    raise ValueError('Not a valid package specification', string)
