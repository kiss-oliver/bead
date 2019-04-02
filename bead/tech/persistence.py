'''
Functions to persist python objects or load them.
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import json

# json is used for serializing objects for persistence as it is
# - in the standard library from >=2.6 (including 3.*)
# - 2.7 version decodes strings as unicode, unlike e.g. the csv module
# - the interface is also becoming the standard one for serialization,
#   e.g. the competing plistlib's interface was deprecated in 3.4 in
#   favor of a new json-like one


if hasattr(json, 'JSONDecodeError'):
    JSONDecodeError = json.JSONDecodeError
else:
    JSONDecodeError = ValueError


class ReadError(Exception):
    """Error loading JSON"""


def load(istream):
    try:
        return json.load(istream)
    except JSONDecodeError as e:
        raise ReadError(e)


def loads(string):
    try:
        return json.loads(string)
    except JSONDecodeError as e:
        raise ReadError(e)


JSON_SAVE_OPTIONS = dict(
    indent=4,
    sort_keys=True,
    ensure_ascii=True,
)


def dumps(content):
    return json.dumps(content, **JSON_SAVE_OPTIONS)


def dump(content, ostream):
    json.dump(content, ostream, **JSON_SAVE_OPTIONS)
