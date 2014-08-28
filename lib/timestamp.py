from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from datetime import tzinfo, timedelta, datetime

ZERO = timedelta(0)
HOUR = timedelta(hours=1)


# source: https://docs.python.org/2/library/datetime.html#tzinfo-objects
class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


TIMESTAMP_FORMAT = '%Y%m%d_%H%M%S_%f'


def timestamp():
    return datetime.now(UTC()).strftime(TIMESTAMP_FORMAT)


def time_from_timestamp(date_string):
    return (
        datetime
        .strptime(date_string, TIMESTAMP_FORMAT)
        .replace(tzinfo=UTC())
    )
