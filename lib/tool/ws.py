from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from mando.core import Program

from ..path import Path
from ..pkg import pkg_dir
from ..pkg import pkg_zip
from ..timestamp import timestamp

from .. import VERSION

main = Program('ws', VERSION)
arg = main.arg
command = main.command


def new(name):
    '''
    Create new package directory layout.
    '''
    pkg_dir.create(name)
    print('Created {}'.format(name))

command(new)


@command
def develop(name, package_file_name):
    '''
    Unpack a package as a source tree.

    Package directory layout is created, but only the source files are
    extracted.
    '''
    dir = Path(name)
    pkg = pkg_zip.Package(package_file_name)
    pkg.extract_dir(pkg_zip.CODE_PATH, dir)
    # FIXME: extracted PKGMETA needs a rewrite
    # as it contains different things in the development and archive format
    pkg.extract_file(pkg_zip.META_PKGMETA, dir / pkg_dir.PKGMETA)
    pkg_dir.create_directories(dir)
    assert pkg_dir.is_valid(dir)
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
    import os
    from ..pkg import cmd_archive
    tempname = cmd_archive.create('.')

    with pkg_zip.Package(tempname) as pkg:
        version = pkg.version

    zipfilename = (
        pkg_dir.TEMP / (
            '{package}_{timestamp}_{version}.zip'
            .format(
                package=pkg_dir.get_package_name(),
                timestamp=timestamp(),
                version=version,
            )
        )
    )
    os.rename(tempname, zipfilename)
    print('Package created at {}'.format(zipfilename))


if __name__ == '__main__':
    main()
