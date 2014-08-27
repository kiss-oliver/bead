from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
from mando.core import Program

from ..path import Path
from ..pkg import workspace
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
    workspace.create(name)
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
            layouts.Archive.META_PKGMETA,
            dir / layouts.Workspace.PKGMETA
        )

    workspace.create_directories(dir)
    assert workspace.is_valid(dir)

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
    tempname = archive.create('.')

    with archive.Archive(tempname) as pkg:
        version = pkg.version

    zipfilename = (
        layouts.Workspace.TEMP / (
            '{package}_{timestamp}_{version}.zip'
            .format(
                package=workspace.get_package_name(),
                timestamp=timestamp(),
                version=version,
            )
        )
    )
    os.rename(tempname, zipfilename)

    print('Package created at {}'.format(zipfilename))
