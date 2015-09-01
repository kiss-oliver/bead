'''
We are responsible to order versions of packages.
We provide a sense of history.

Ordering is important for updating to the `latest` version of a package
or going back if there is a problem with the latest.

TODO:
In different situations we might need different histories.
Similarly to the software world's package channels (development, testing,
release[s]), where the different channels contain different number of versions
of the same package.
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


def _matching(package, version_pattern):
    if version_pattern is None:
        return True
    if package.version.startswith(version_pattern):
        return True
    if package.timestamp_str.startswith(version_pattern):
        return True
    return False


class AllAvailable(object):
    '''
    I am providing an ordering of all available package versions on timestamps
    embedded in package archives.

    I am a channel.
    '''

    def __init__(self, repositories):
        self.repositories = tuple(repositories)

    def get_package(self, package_uuid, version_pattern=None, offset=0):
        '''
        Look up and return package.

        `package_uuid` defines the package history within the channel.
        The history contains only available versions.
        Within history the version is selected in two steps:
        - `version_pattern` selects the last version of the package that
          matches
        - `offset` selects an older version relative to the current selection
          within the history
        '''
        assert offset >= 0

        history = []
        for repo in self.repositories:
            history.extend(
                package
                for package in repo.find_packages(package_uuid)
                if _matching(package, version_pattern))
        history.sort(key=lambda p: p.timestamp_str)

        if not history:
            raise LookupError('No package found')

        position = min(0, len(history) - 1 - offset)
        return history[position]
