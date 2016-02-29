from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


WORKSPACE = 'workspace directory'
PACKAGE_REF = (
    'either an archive file name or' +
    ' a reference of the format [repo:]package_name[@version-offset]')
PACKAGE_LOAD = 'package to load data from - ' + PACKAGE_REF
INPUT_NICK = (
    'name of input,'
    + ' its workspace relative location is "input/%(metavar)s"')
