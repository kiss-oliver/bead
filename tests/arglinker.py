'''
Enable a py.test like automatic fixture injection with subclassing
the TestCase provided (derived from unittest.TestCase)

Fixtures will be automatically passed as the appropriate parameters of
the test methods of the linked class.

Fixture `a` is defined as the return value of non-test method `a()`
of the same TestCase derived class.
'''

import functools
import inspect
import unittest


__all__ = ['TestCase']


def call_with_fixtures(obj, function, fixtures):
    args = inspect.getfullargspec(function).args[1:]
    for arg in args:
        add_fixture(obj, arg, fixtures)
    # python2: `self` must be positional parameter, not keyword parameter
    return function(obj, **dict((arg, fixtures[arg]) for arg in args))


def add_fixture(obj, arg_name, fixtures):
    if arg_name in fixtures:
        return
    create_fixture = getattr(obj.__class__, arg_name)
    fixture = call_with_fixtures(obj, create_fixture, fixtures)
    fixtures[arg_name] = fixture


def func_with_fixture_resolver(f):
    argspec = inspect.getfullargspec(f)
    does_not_need_transform = (
        argspec.args == ['self'] or argspec.varargs or argspec.varkw
    )
    if does_not_need_transform:
        return f

    # strong python convention: subject of method is named self
    # assumption: developers follow convention
    assert argspec.args[0] == 'self'

    @functools.wraps(f)
    def f_with_fixtures(self):
        return call_with_fixtures(self, f, fixtures={})

    return f_with_fixtures


class ArgLinkerMeta(type):
    '''
    Metaclass linking fixtures to parameter names.

    Replaces test methods with closure methods that create/resolve fixtures
    from parameter names and call the original test method with the fixtures.
    '''

    def __new__(cls, name, parents, dct):
        new_dct = {}
        for obj_name, obj in dct.items():
            is_test_method = (
                obj_name.startswith('test') and inspect.isfunction(obj))
            if is_test_method:
                new_dct[obj_name] = func_with_fixture_resolver(obj)
            else:
                new_dct[obj_name] = obj

        return (
            super(ArgLinkerMeta, cls).__new__(cls, name, parents, new_dct))


class TestCase(unittest.TestCase, metaclass=ArgLinkerMeta):
    pass
