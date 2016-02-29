from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import re
from collections import namedtuple


# TODO: parse and return 'offset' - "offset to last matching version"
PackageSpec = namedtuple('PackageSpec', 'repo name version offset')
ALL_REPOSITORIES = object()


_parse = re.compile(
    r'''
    ^
    # repo is optional
    (
        (?P<repo>[^:@]*)
        :
    )?

    # name is mandatory
    (?P<name>[^:@]+)

    # version is optional
    (
        @
        (?P<version>[^-:@]+)?
        (-(?P<offset>[0-9]+))?
    )?
    $
    ''', re.VERBOSE).match


def parse(string):
    '''
    Parse a string based package specification.

    Parts of the returned package specification:
    - repo (optional, defaults to all repositories)
    - name (mandatory)
    - version (optional, defaults to None)
    '''
    match = _parse(string)
    if match:
        m = match.groupdict()
        return PackageSpec(
            m['repo'] or ALL_REPOSITORIES,
            m['name'],
            m['version'],
            int(m['offset'] or '0'))
    raise ValueError('Not a valid package specification', string)
