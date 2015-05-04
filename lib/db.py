from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import omlite
from .translations import Peer, Translation


def initialize_new_db():
    '''
    Initialize a new empty database, that is already connected to by omlite.
    '''
    omlite.create_table(Peer)
    omlite.create_table(Translation)

    _create_self()


def _create_self():
    # create self as peer with special empty name
    self = Peer(name='')
    omlite.create(self)
    self.value = self.id
    omlite.save(self)
