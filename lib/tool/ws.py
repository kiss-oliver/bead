from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from mando.core import Program

import os
from ..path import Path
from ..pkg.workspace import Workspace
from ..pkg import archive
from ..pkg import layouts
from ..pkg import meta
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


def find_package(repo_dir, package_uuid, package_version):
    for candidate in os.listdir(repo_dir):
        try:
            package = archive.Archive(candidate)
            if package.uuid == package_uuid:
                if package.version == package_version:
                    return repo_dir / candidate
        except:
            pass


@command
def develop(name, package_file_name, mount=False):
    '''
    Unpack a package as a source tree.

    Package directory layout is created, but only the source files are
    extracted.
    '''
    dir = Path(name)
    workspace = Workspace(dir)

    with archive.Archive(package_file_name) as pkg:
        pkg.extract_dir(layouts.Archive.CODE, dir)
        # extracted PKGMETA needs a rewrite
        # as it contains different things in the development and archive format
        archive_meta = pkg.meta
        development_meta = {
            meta.KEY_PACKAGE: archive_meta[meta.KEY_PACKAGE],
            # this baby repo can be used to mount packages for demo purposes
            # that is, until we have a proper repo
            meta.KEY_BABY_REPO: os.path.abspath(os.path.dirname(dir)),
            meta.KEY_INPUTS: {
                nick: {
                    meta.KEY_INPUT_MOUNTED: False,
                    meta.KEY_INPUT_PACKAGE: spec[meta.KEY_INPUT_PACKAGE],
                    meta.KEY_INPUT_VERSION: spec[meta.KEY_INPUT_VERSION],
                }
                for nick, spec in archive_meta[meta.KEY_INPUTS].items()
            },
        }
        workspace.meta = development_meta

    workspace.create_directories()
    assert workspace.is_valid

    if mount:
        baby_repo = workspace.meta[meta.KEY_BABY_REPO]
        input = workspace.meta[meta.KEY_INPUTS]
        for nick, spec in input.items():
            package_file_name = find_package(
                Path(baby_repo),
                spec[meta.KEY_INPUT_PACKAGE],
                spec[meta.KEY_INPUT_VERSION],
            )
            workspace.mount(nick, archive.Archive(package_file_name))

    print('Extracted source into {}'.format(dir))
    print_mounts(directory=dir)


@arg('package_file_name', metavar='<package file name>')
def mount(nick, package_file_name):
    '''
    Add data to input directory.

    aliases: mount, add-input
    '''
    workspace = Workspace()
    pkg = archive.Archive(package_file_name)
    assert not workspace.has_input(nick)
    workspace.mount(nick, pkg)
    assert workspace.has_input(nick)

command(mount)
command('add-input')(mount)


def print_mounts(directory):
    workspace = Workspace(directory)
    inputs = workspace.meta[meta.KEY_INPUTS]
    if not inputs:
        print('Package has no defined inputs, yet')
    else:
        print('Package inputs')
        for nick in sorted(inputs):
            print(
                '{}: {}mounted'
                .format(nick, '' if workspace.is_mounted(nick) else 'not ')
            )


@command('mounts')
def mounts():
    '''Show mount names and their status'''
    print_mounts('.')


def unmount(nick):
    '''
    TODO - Remove data from input directory.

    aliases: unmount, umount, forget-input
    '''
    pass

command(unmount)
command('umount')(unmount)
command('forget-input')(unmount)


@command
def update(nick, package_file_name):
    '''TODO - replace input <nick> with a newer version
    '''
    pass


@command
def pack():
    '''Create a new archive from the workspace'''
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
