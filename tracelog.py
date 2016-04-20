'''
Logging during tests with human readable output to file.

Much simpler than logging: this is intended to be used only from test code.

Command line usage:
    $ TRACELOG=traces.log ./test

Beware of multi-process capable runners: they will interweave messages.
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import atexit
from datetime import datetime
import inspect
import os


__all__ = ('TRACELOG')


trace_file_name = os.environ.get('TRACELOG')
trim_path = os.path.dirname(__file__) + os.path.sep

trace_file = None
if trace_file_name:
    trace_file = open(trace_file_name, 'a')

test_function = None


def _cleanup():
    global trace_file
    global test_function
    test_function = None

    _write('END')
    if trace_file:
        trace_file.close()
    trace_file = None

atexit.register(_cleanup)


def _get_test(stack):
    for _frame, filename, lineno, function, code_context, _index in stack:
        if function.startswith('test'):
            return '{} {}()'.format(_shorten(filename), function)


def _shorten(filepath):
    relpath = os.path.relpath(filepath, trim_path)
    if len(relpath) < len(filepath):
        return relpath
    return filepath


def _write(message):
    if trace_file:
        trace_file.write(message)
        trace_file.write('\n')


def TRACELOG(*args, **kwargs):
    global test_function

    if not trace_file:
        return

    now = datetime.now()
    stack = inspect.stack()

    # assume calls from tests
    test = _get_test(stack)
    if test != test_function:
        if test_function:
            _write('{time} END OF TRACELOG FROM TEST {test}\n'.format(time=now, test=test_function))
        test_function = test
        if test_function:
            _write('\n{time} TRACELOG FROM TEST {test}'.format(time=now, test=test_function))

    # caller info
    _frame, filename, lineno, function, _code_context, _index = stack[1]

    location = '{filename}:{lineno:<4d} @{function:5s}'.format(
        filename=_shorten(filename), lineno=lineno, function=function)

    message = ' '.join(repr(arg) for arg in args)
    if kwargs:
        message += '   ** ' + ' | '.join('{}: {!r}'.format(key, value) for key, value in sorted(kwargs.items()))

    if test_function:
        # we have time in the test header-footer
        _write('  {location} {message}'.format(location=location, message=message))
    else:
        _write('{time} {location} {message}'.format(time=now, location=location, message=message))
