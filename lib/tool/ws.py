from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from mando.core import Program

from ..path import Path
from ..pkg.workspace import Workspace
from ..pkg import archive
from ..pkg import layouts
from ..timestamp import timestamp

from .. import VERSION

main = Program('ws', VERSION)
arg = main.arg
command = main.command


@command
def new(name):
    '''
    Create new package directory layout.
    '''
    Workspace(name).create()
    print('Created {}'.format(name))


@command
def develop(name, package_file_name):
    '''
    Unpack a package as a source tree.

    Package directory layout is created, but only the source files are
    extracted.
    '''
    dir = Path(name)
    with archive.Archive(package_file_name) as pkg:
        pkg.extract_dir(layouts.Archive.CODE, dir)
        # FIXME: extracted PKGMETA needs a rewrite
        # as it contains different things in the development and archive format
        pkg.extract_file(
            layouts.Archive.PKGMETA,
            dir / layouts.Workspace.PKGMETA
        )
        # TODO: try to mount all inputs

    Workspace(dir).create_directories()
    assert Workspace(dir).is_valid

    print('Extracted source into {}'.format(dir))


@arg('package_file_name', metavar='<package file name>')
def mount(nick, package_file_name):
    '''
    Add data to input directory.

    aliases: mount, add-input
    '''
    pass

command(mount)
command('add-input')(mount)


def unmount(nick):
    '''
    Remove data from input directory.

    aliases: unmount, umount, forget-input
    '''
    pass

command(unmount)
command('umount')(unmount)
command('forget-input')(unmount)


@command
def update(nick, package_file_name):
    '''TODO
    '''
    pass


@command
def pack():
    workspace = Workspace()
    ts = timestamp()
    zipfilename = (
        Path('.') / layouts.Workspace.TEMP / (
            '{package}_{timestamp}.zip'
            .format(
                package=workspace.package_name,
                timestamp=ts,
            )
        )
    )
    workspace.pack(zipfilename, timestamp=ts)

    print('Package created at {}'.format(zipfilename))
