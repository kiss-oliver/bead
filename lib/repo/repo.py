from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


'''
packages are stored in the hierarchy

repo_root
    |- package-names.yaml
    |- packages
        |- pkg_uuid
            |- version_uuid
                |- data.pkg
                |- informal-name.txt
                |- tags
                    |- tag1
                    |- tag2
                    |- ...
    |- channel-names.yaml
    |- channels
        |- ???
'''


class Repo(object):

    def __init__(self, repo_root):
        pass

    def get_package_root(self, pkg_uuid, version_uuid):
        return (
            self.root
            / pkg_uuid[:3] / pkg_uuid[3:]
            / version_uuid[:8] / version_uuid[8:]
        )

    def get_package_mnemonic(self, pkg_uuid):
        # TODO
        pass

    def set_package_mnemonic(self, pkg_uuid, pkg_mnemonic):
        # TODO
        pass

    def get_package_uuid(self, pkg_mnemonic):
        # TODO
        pass

    def get_package_timestamp(self, pkg_uuid, version_uuid):
        # TODO
        pass
