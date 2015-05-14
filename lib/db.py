from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os

import omlite
from .translations import Peer, Translation


MEMORY = ':memory:'


def connect(db_path):
    existing = db_path != MEMORY and os.path.exists(db_path)
    omlite.db.connect(db_path)

    try:
        if not existing:
            initialize_new_db()
    except:
        omlite.db.connect(MEMORY)
        # remove newly created, but partially initialized database
        os.remove(db_path)
        raise


def initialize_new_db():
    '''
    Initialize a new empty database, that is already connected to by omlite.
    '''
    omlite.create_table(Peer)
    omlite.create_table(Translation)

    _create_self()


def _create_self():
    # create self as peer with special empty name
    with omlite.db.transaction():
        self = Peer(name='')
        omlite.create(self)
        self.value = self.id
        omlite.save(self)
