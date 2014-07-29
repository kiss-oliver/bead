'''
Archive layout of packages
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import yaml

from .path import Path


DATA_PATH = Path('data')
CODE_PATH = Path('code')
META_PATH = Path('meta')

META_PKGMETA_YAML = META_PATH / 'pkgmeta.yaml'
META_CHECKSUMS = META_PATH / 'checksums.sha512'


def to_yaml(obj):
    return yaml.safe_dump(
        obj,
        encoding='utf-8', allow_unicode=True,
        indent=2,
        default_style=False,
        default_flow_style=False,
    )
