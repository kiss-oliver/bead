from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import time
from datetime import tzinfo, timedelta, datetime


# source: https://docs.python.org/2/library/datetime.html
# Example tzinfo classes:
# A class capturing the platform's idea of local time.

import time as _time

ZERO = timedelta(0)

STDOFFSET = timedelta(seconds = -_time.timezone)
if _time.daylight:
    DSTOFFSET = timedelta(seconds = -_time.altzone)
else:
    DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET

class LocalTimezone(tzinfo):

    def utcoffset(self, dt):
        if self._isdst(dt):
            return DSTOFFSET
        else:
            return STDOFFSET

    def dst(self, dt):
        if self._isdst(dt):
            return DSTDIFF
        else:
            return ZERO

    def tzname(self, dt):
        return _time.tzname[self._isdst(dt)]

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, 0)
        stamp = _time.mktime(tt)
        tt = _time.localtime(stamp)
        return tt.tm_isdst > 0

Local = LocalTimezone()


#
TIMESTAMP_FORMAT = '%Y%m%dT%H%M%S%f%z'


def timestamp():
    return datetime.now(Local).strftime(TIMESTAMP_FORMAT)


def time_from_timestamp(date_string):
    return datetime.strptime(date_string, TIMESTAMP_FORMAT)


ISO8601_FORMATS = (
    '%Y',
    '%Y%m',
    '%Y%m%d',
    '%Y%m%dT%H%M%S%z',
    '%Y%m%dT%H%M%S%f%z',
    )


def parse_iso8601(str):
    for fmt in ISO8601_FORMATS:
        try:
            return datetime.strptime(str, fmt)
        except ValueError:
            # maybe the next format
            pass
    raise ValueError('Invalid datetime', str)


def parse_user_timestamp(str):
    try:
        return parse_iso8601(str)
    except ValueError:
        # fall back to interpreting it as a time-delta added to `now`
        # FIXME: implement parse_timedelta()
        return datetime.now(Local) + parse_timedelta(str)
