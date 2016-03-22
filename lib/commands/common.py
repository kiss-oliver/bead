from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from argh.decorators import arg
import os
import sys

from .. import repos

from ..pkg.workspace import Workspace, CurrentDirWorkspace
from ..pkg.archive import Archive
from ..pkg import spec as pkg_spec
from . import arg_help
from . import arg_metavar

ERROR_EXIT = 1


def die(msg):
    sys.stderr.write('ERROR: ')
    sys.stderr.write(msg)
    sys.stderr.write('\n')
    sys.exit(ERROR_EXIT)


def warning(msg):
    sys.stderr.write('WARNING: ')
    sys.stderr.write(msg)
    sys.stderr.write('\n')


def opt_workspace(func):
    '''
    Define `workspace` as option, defaulting to current directory
    '''
    decorate = arg(
        '--workspace', '-w', metavar=arg_metavar.WORKSPACE,
        type=Workspace, default=CurrentDirWorkspace(),
        help=arg_help.WORKSPACE)
    return decorate(func)


class DefaultArgSentinel(object):
    '''
    I am a sentinel for @argh.arg default values.

    I.e. If you see me, it means that you got the default value.

    I also provide sensible description for the default value.
    '''

    def __init__(self, description):
        self.description = description

    def __repr__(self):
        return self.description


def package_spec_kwargs(func):
    # TODO: implement more options
    for modifier in [
        # -r, --repo, --repository

        # package_filters
        arg('-o', '--older', '--older-than', dest='older_than', metavar='TIMEDELTA'),
        arg('-n', '--newer', '--newer-than', dest='newer_than', metavar='TIMEDELTA'),
        arg('-d', '--date', dest='date'),

        # match reducers
        # -N, --next
        # -P, --prev, --previous
        # --newest, --latest (default)
        # --oldest
    ]:
        func = modifier(func)
    return func


def parse_package_spec_kwargs(kwargs):
    arg_to_filter = {
        'older_than': pkg_spec.older_than,
        'newer_than': pkg_spec.newer_than,
        'date': pkg_spec.timestamp_prefix,
    }
    query = pkg_spec.PackageQuery()
    for attr in arg_to_filter:
        query.add_package_filter(arg_to_filter[attr](kwargs[attr]))
    return query



# TODO: delete experimental code

if __name__ == '__main__':
    # parse time-delta
    # TODO: make
    import re
    re.match(r'(([+-]?\d+) *([ymwdHMS]))*$', '2w12H  13M')
    re.findall(r'([+-]?\d+) *([ymwdHMS])', 'asd +-12H +13M x')

    from argh import ArghParser, arg, named
    @named('get')
    @package_spec_kwargs
    def cmd(other, **kwargs):
        spec = parse_package_spec_kwargs(kwargs)
        print(spec.package_filters)
        print(other, kwargs)

    p = ArghParser()
    # p.set_default_command(cmd)
    p.add_commands([cmd])
    p.dispatch()
