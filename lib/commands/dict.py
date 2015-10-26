from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


from argh.decorators import named
from ..translations import Peer, add_translation, import_translations


def add(name, package_uuid):
    add_translation(name, package_uuid)


def export(filename, peer=Peer.SELF):
    Peer.by_name(peer).export(filename)


@named('import')
def import_(peer, filename):
    import_translations(peer, filename)


def rename(old_name, new_name):
    self = Peer.self()
    translation = self.get_translation(old_name)
    translation.name = new_name
    translation.save()


def forget(name):
    self = Peer.self()
    translation = self.get_translation(name)
    translation.delete()


def merge(peer):
    self = Peer.self()
    source = Peer.by_name(peer)
    for translation in source.all_translations():
        if self.knows_about(translation.name):
            # assert False, translation.name
            pass
        else:
            add_translation(
                translation.name, translation.package_uuid)
