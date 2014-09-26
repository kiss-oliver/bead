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
from ..pkg import metakey
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
        workspace.create_directories()

        # extracted PKGMETA needs a rewrite
        # as it contains different things in the development and archive format
        archive_meta = pkg.meta
        development_meta = {
            metakey.PACKAGE: archive_meta[metakey.PACKAGE],
            metakey.INPUTS: {
                nick: {
                    metakey.INPUT_MOUNTED: False,
                    metakey.INPUT_PACKAGE: spec[metakey.INPUT_PACKAGE],
                    metakey.INPUT_VERSION: spec[metakey.INPUT_VERSION],
                }
                for nick, spec in archive_meta[metakey.INPUTS].items()
            },
        }
        workspace.meta = development_meta
        # this flat repo can be used to mount packages for demo purposes
        # that is, until we have a proper repo
        workspace.flat_repo = os.path.abspath(
            os.path.dirname(package_file_name)
        )

    assert workspace.is_valid

    if mount:
        mount_all(workspace)

    print('Extracted source into {}'.format(dir))
    print_mounts(directory=dir)


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


def find_package(repo_dir, package_uuid, package_version):
    for name in os.listdir(repo_dir):
        candidate = repo_dir / name
        try:
            package = archive.Archive(candidate)
            if package.uuid == package_uuid:
                if package.version == package_version:
                    return candidate
        except:
            pass


def mount_nick(workspace, nick):
    assert workspace.has_input(nick)
    if not workspace.is_mounted(nick):
        spec = workspace.meta[metakey.INPUTS][nick]
        package_file_name = find_package(
            Path(workspace.flat_repo),
            spec[metakey.INPUT_PACKAGE],
            spec[metakey.INPUT_VERSION],
        )
        if package_file_name is None:
            print('Could not find archive for {} - not mounted!'.format(nick))
            return
        workspace.mount(nick, archive.Archive(package_file_name))
        print('Mounted {}.'.format(nick))


def mount_all(workspace):
    for nick in workspace.meta[metakey.INPUTS]:
        mount_nick(workspace, nick)


def mount_archive(workspace, nick, package_file_name):
    assert not workspace.has_input(nick)
    workspace.mount(nick, archive.Archive(package_file_name))
    print('{} mounted on {}.'.format(package_file_name, nick))


@arg('nick', nargs='?')
@arg('package_file_name', nargs='?', metavar='package file name')
def mount(nick, package_file_name):
    '''
    Add data to input directory.

    aliases: mount, add-input
    '''
    workspace = Workspace()
    if nick is None:
        mount_all(workspace)
    elif package_file_name is None:
        mount_nick(workspace, nick)
    else:
        mount_archive(workspace, nick, package_file_name)

command(mount)
# command('add-input')(mount)


def print_mounts(directory):
    workspace = Workspace(directory)
    inputs = workspace.meta[metakey.INPUTS]
    if not inputs:
        print('Package has no defined inputs, yet')
    else:
        print('Package inputs:')
        for nick in sorted(inputs):
            print(
                '  {}: {}mounted'
                .format(nick, '' if workspace.is_mounted(nick) else 'not ')
            )


@command('mounts')
def mounts():
    '''Show mount names and their status'''
    print_mounts('.')


def unmount(nick):
    '''
    INTERNAL: Remove data from input directory.
    '''
    Workspace().unmount(nick)
    print('{} is unmounted.'.format(nick))

command(unmount)


def delete_input(nick):
    '''Forget input'''
    Workspace().delete_input(nick)
    print('Input {} is deleted.'.format(nick))

command('delete-input')(delete_input)


@command
def update(nick, package_file_name):
    '''TODO: replace input with a newer version
    '''
    pass
