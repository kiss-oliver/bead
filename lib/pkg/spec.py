from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import re
from collections import namedtuple


# TODO: parse and return 'offset' - "offset to last matching version"
PackageSpec = namedtuple('PackageSpec', 'peer name version')


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
        (?P<version>[^:@]+)
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
        return PackageSpec(m['peer'] or '', m['name'], m['version'])
    raise ValueError('Not a valid package specification', string)
