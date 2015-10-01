from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from argh.decorators import arg
import os
import sys

# get_channel
from .. import channels
from .. import repos

from ..pkg.workspace import Workspace, CurrentDirWorkspace
from ..pkg.archive import Archive
from ..pkg.spec import parse as parse_package_spec
from ..translations import Peer
from . import help
from . import metavar

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
        '--workspace', metavar=metavar.WORKSPACE,
        type=Workspace, default=CurrentDirWorkspace(),
        help=help.WORKSPACE)
    return decorate(func)


class PackageReference(object):
    def __init__(self, package_reference):
        self.package_reference = package_reference

    @property
    def package(self):
        if os.path.isfile(self.package_reference):
            return Archive(self.package_reference)

        package_spec = parse_package_spec(self.package_reference)
        peer = Peer.by_name(package_spec.peer)
        package_translation = peer.get_translation(package_spec.name)
        uuid = package_translation.package_uuid
        package = (
            get_channel()
            .get_package(uuid, package_spec.version, package_spec.offset))
        return package

    @property
    def default_workspace(self):
        if os.path.isfile(self.package_reference):
            archive_filename = os.path.basename(self.package_reference)
            workspace_dir = os.path.splitext(archive_filename)[0]
        else:
            package_spec = parse_package_spec(self.package_reference)
            workspace_dir = package_spec.name
        return Workspace(workspace_dir)


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


def get_channel():
    return channels.AllAvailable(repos.get_all())
