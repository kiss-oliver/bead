from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from mando.core import Program

main = Program('lib', '0.0.1-dev')
arg = main.arg
command = main.command


# repo
@command('new-repo')
def new_repo():
    '''\
    Create a new repository for data packages.
    '''
    # TODO: command new-repo
    print('new repo created')


@command
@arg('repo', '--repo', default='origin')
@arg('package', '--package', default='', metavar='NAME')
@arg('new_name', metavar='NEW-NAME')
def rename(repo, package, new_name):
    '''\
    Rename package in repository

    :param repo: repository in which to rename package (default: %(default)s)
    :param package: package name to change
                    (defaults to package developed in current directory)
    '''
    pass


# packages
@command('new-package')
def new_package():
    pass


@command
def register(repo, package_name):
    '''\
    register the package with a repo
    '''
    pass


@command
def develop(name, version='latest'):
    pass


@command
def mount(nick, package_name, version='latest'):
    pass


@command
def unmount(nick):
    pass


@command
def update(nick, version='latest'):
    pass


@command
def pack():
    pass


@command
def publish(repo='origin'):
    pass


# data end users
@command('get-data')
def get_data():
    '''\
    Extract data for data end users.

    Refuses to work under another package's directory (=developers).
    '''


if __name__ == '__main__':
    main()
