from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os

from ..import repos


def add(name, directory):
    '''
    Define a repository.
    '''
    if not os.path.isdir(directory):
        print('ERROR: "{}" is not an existing directory!'.format(directory))
        return
    location = os.path.abspath(directory)
    try:
        repos.add(name, location)
        print('Will remember repo {}'.format(name))
    except ValueError as e:
        print('ERROR:', *e.args)
        print('Check the parameters: both name and directory must be unique!')


def list():
    '''
    List repositories.
    '''
    repositories = repos.get_all()

    def print_repo(repo):
        print('{0.name}: {0.location}'.format(repo))
    try:
        repo = next(repositories)
    except StopIteration:
        print('There are no defined repositories')
    else:
        # XXX use tabulate?
        print('Repositories:')
        print('-------------')
        print_repo(repo)
        for repo in repositories:
            print_repo(repo)


def forget(name):
    '''
    Remove the named repository from the repositories known by the tool.
    '''
    if repos.is_known(name):
        repos.forget(name)
        print('Repository "{}" is forgotten'.format(name))
    else:
        print('WARNING: no repository defined with "{}"'.format(name))
