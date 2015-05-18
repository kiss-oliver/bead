from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from .test import TestCase
import omlite

from .translations import (
    Peer, Translation, add_translation, import_translations,
)
from .db import initialize_new_db


class TestCase(TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.new_db()

    def new_db(self):
        omlite.db.connect(':memory:')
        initialize_new_db()

    def assert_peer_eq(self, peer1, peer2):
        self.assertEqual(
            (peer1.id, peer1.name),
            (peer2.id, peer2.name),
        )

    def assert_translation_eq(self, t1, t2):
        self.assertEqual(
            (t1.id, t1.peer_id, t1.name, t1.package_uuid),
            (t2.id, t2.peer_id, t2.name, t2.package_uuid),
        )


class Test_Peer(TestCase):

    def test_peer_name_is_unique(self):
        Peer('a').save()
        self.assertRaises(omlite.IntegrityError, Peer('a').save)

    def test_self_is_a_peer(self):
        self_peer = Peer.self()
        self.assertIsInstance(self_peer, Peer)
        self.assertEqual('', self_peer.name)
        self.assertIsNotNone(self_peer.id)

    def test_by_name(self):
        a = Peer('a')
        a.save()
        a_from_db = Peer.by_name('a')
        self.assert_peer_eq(a, a_from_db)

    def test_by_name_with_unknown_peer_raises_LookupError(self):
        self.assertRaises(LookupError, Peer.by_name, 'a')
        self.assertRaises(LookupError, Peer.by_name, 'unknown peer')

    def test_create_a_new_self(self):
        old_self = Peer.self()
        old_self_id = old_self.id
        omlite.delete(old_self)

        new_self = Peer('')
        new_self.save()

        self.assertIsNotNone(new_self.id)
        self.assertNotEqual(old_self_id, new_self.id)
        self.assert_peer_eq(new_self, Peer.self())

    def test_knows_about(self):
        self.assertFalse(Peer.self().knows_about('nonexisting'))
        add_translation('existing package', 'uuid')
        self.assertTrue(Peer.self().knows_about('existing package'))

    def test_get_translation(self):
        a = Peer('a')
        a.save()
        translation = Translation()
        translation.peer_id = a.id
        translation.name = 'shiny'
        translation.package_uuid = 'can not guess'
        omlite.save(translation)
        result = a.get_translation('shiny')
        self.assert_translation_eq(translation, result)

    def test_get_translation_nonexisting_name_raises_LookupError(self):
        a = Peer('a')
        a.save()
        self.assertRaises(LookupError, a.get_translation, 'nonexisting')


class Test_Translation(TestCase):

    def test_delete_peer_deletes_its_children(self):
        self.given_a_database_with_two_peers_and_package_translations()
        self.when_deleting_one_peer()
        self.then_only_the_other_peer_and_its_package_translations_remain()

    def given_a_database_with_two_peers_and_package_translations(self):
        def create_peer_and_translation(n):
            peer = Peer(name='peer {}'.format(n))
            omlite.save(peer)
            translation = Translation()
            translation.peer_id = peer.id
            translation.name = 'translation {}'.format(n)
            translation.package_uuid = 'package uuid {}'.format(n)
            omlite.save(translation)
            return peer, translation

        self.peer1, self.translation1 = create_peer_and_translation(1)
        self.peer2, self.translation2 = create_peer_and_translation(2)

    def when_deleting_one_peer(self):
        omlite.delete(self.peer1)

    def then_only_the_other_peer_and_its_package_translations_remain(self):
        self.assertRaises(
            LookupError, omlite.get, Peer, self.peer1.id)
        self.assertRaises(
            LookupError, omlite.get, Translation, self.translation1.id)
        peer_names = [t.name for t in omlite.filter(Peer, '1 == 1')]
        pkg_names = [t.name for t in omlite.filter(Translation, '1 == 1')]
        self.assertEqual(set(['', 'peer 2']), set(peer_names))
        self.assertEqual(set(['translation 2']), set(pkg_names))


class Test_export_import(TestCase):

    def test_exported_packages_can_be_imported(self):
        self.given_a_database_with_package_translations()
        self.when_exporting_all_package_translations()
        self.then_another_user_can_import_the_exported_file()

    def test_import_replaces_all_translations_from_same_peer(self):
        self.given_two_exported_file_with_differences_from_the_same_peer()
        self.when_importing_the_files()
        self.then_only_the_last_imported_data_is_visible()

    #
    exported_names1 = str

    def given_a_database_with_package_translations(self):
        add_translation('name1', 'uuid1')
        add_translation('name2', 'uuid1')
        add_translation('name3', 'uuid2')

    def dump(self):
        filename = self.new_temp_filename()
        Peer.self().export(filename)
        return filename

    def when_exporting_all_package_translations(self):
        self.exported_names1 = self.dump()

    def then_another_user_can_import_the_exported_file(self):
        old_self = Peer.self()
        orig_translation = old_self.get_translation('name1')
        self.new_db()
        self.assertNotEqual(old_self.id, Peer.self().id)

        import_translations('imported peer', self.exported_names1)

        peer = Peer.by_name('imported peer')
        self.assertEqual(old_self.id, peer.id)
        translation = peer.get_translation('name1')
        self.assert_translation_eq(translation, orig_translation)

    def given_two_exported_file_with_differences_from_the_same_peer(self):
        self.given_a_database_with_package_translations()
        self.exported_names1 = self.dump()

        # modify data
        omlite.delete(Peer.self().get_translation('name3'))
        add_translation('name9', 'uuid9')

        self.exported_names2 = self.dump()

    def when_importing_the_files(self):
        self.new_db()
        add_translation('untouchable', 'uuid1')
        import_translations('imported peer - 1', self.exported_names1)
        import_translations('imported peer - 2', self.exported_names2)

    def then_only_the_last_imported_data_is_visible(self):
        self.assertRaises(LookupError, Peer.by_name, 'imported peer - 1')
        peer = Peer.by_name('imported peer - 2')
        peer.get_translation('name1')
        peer.get_translation('name2')
        peer.get_translation('name9')
        # name3 is not in the second dump
        self.assertRaises(LookupError, peer.get_translation, 'name3')
        # package named by me is still available
        Peer.self().get_translation('untouchable')


if __name__ == '__main__':
    unittest.main()
