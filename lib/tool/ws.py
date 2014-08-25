from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from mando.core import Program

from .. import VERSION

main = Program('ws', VERSION)
arg = main.arg
command = main.command


@command()
def init(name):
    pass


@command
def develop(package_file_name):
    pass


@command
def mount(nick, package_file_name):
    pass


@command
def unmount(nick):
    pass


@command
def update(nick, package_file_name):
    pass


@command
def pack():
    import os
    from .pkg import pkg_dir
    from .pkg import pkg_zip
    from .pkg import cmd_archive
    tempname = cmd_archive.create('.')

    with pkg_zip.Package(tempname) as pkg:
        version = pkg.version
    zipfilename = (
        pkg_dir.TEMP / (
            '{package}_{version}.zip'
            .format(pkg_dir.get_package_name(), version)
        )
    )
    os.rename(tempname, zipfilename)


if __name__ == '__main__':
    main()
