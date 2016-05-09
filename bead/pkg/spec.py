from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from fnmatch import fnmatch


# QUERY_ORDER:
NEWEST_FIRST = 'newest_first'
OLDEST_FIRST = 'oldest_first'
# XXX - is there any practical use for this?
# UNSORTED     = 'unsorted'

# QUERY_WHERE:
OLDER_THAN     = 'OLDER_THAN'
NEWER_THAN     = 'NEWER_THAN'
BEAD_NAME_GLOB = 'BEAD_NAME_GLOB'
BEAD_UUID      = 'BEAD_UUID'
CONTENT_HASH   = 'CONTENT_HASH'
# TODO: support shortened content hashes


# private and specific to Repository implementation, when Repository gains
# more power, it should change how it handles queries (e.g. using BEAD_UUID
# or CONTENT_HASH directly through an index)

def _make_checkers():
    def is_newer_than(timestamp):
        def filter(pkg):
            return pkg.timestamp > timestamp
        return filter

    def is_older_than(timestamp):
        def filter(pkg):
            return pkg.timestamp < timestamp
        return filter

    def has_name_glob(nameglob):
        def filter(pkg):
            return fnmatch(pkg.name, nameglob)
        return filter

    def has_uuid(uuid):
        def filter(pkg):
            return pkg.uuid == uuid
        return filter

    def has_content_prefix(hash_prefix):
        def filter(pkg):
            return pkg.version.startswith(hash_prefix)
        return filter

    return {
        OLDER_THAN:     is_older_than,
        NEWER_THAN:     is_newer_than,
        BEAD_NAME_GLOB: has_name_glob,
        BEAD_UUID:      has_uuid,
        CONTENT_HASH:   has_content_prefix,
    }

_CHECKERS = _make_checkers()


def compile_conditions(conditions):
    '''
    Compile list of (check-name, check-param)-s into a match function.
    '''
    checkers = [_CHECKERS[check](param) for check, param in conditions]

    def match(pkg):
        for check in checkers:
            if not check(pkg):
                return False
        return True
    return match
