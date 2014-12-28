from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase
from . import uuid_translator as m

import os
import shutil

A_SCOPE = 'scope'
A_NAME = 'name'
A_UUID = 'uuid'


class Test_uuid_translator(TestCase):

    @property
    def uuid_translator(self):
        return m.uuid_translator(':memory:')

    def test_known_name(self):
        with self.uuid_translator as t:
            t.add(scope=A_SCOPE, name=A_NAME, uuid=A_UUID)
            self.assertEqual(
                A_UUID,
                t.get_uuid(scope=A_SCOPE, name=A_NAME)
            )

    def test_unknown_name(self):
        with self.uuid_translator as t:
            self.assertRaises(
                LookupError,
                t.get_uuid, scope=A_SCOPE, name=A_NAME,
            )

    def test_known_uuid(self):
        with self.uuid_translator as t:
            t.add(scope=A_SCOPE, uuid=A_UUID, name=A_NAME)
            self.assertEqual(
                A_NAME,
                t.get_name(scope=A_SCOPE, uuid=A_UUID)
            )

    def test_unknown_uuid(self):
        with self.uuid_translator as t:
            self.assertRaises(
                LookupError,
                t.get_name, scope=A_SCOPE, uuid=A_UUID,
            )

    def test_add_with_same_scope_and_name_fails(self):
        with self.uuid_translator as t:
            t.add(scope=A_SCOPE, uuid='uuid1', name=A_NAME)
            self.assertRaises(
                m.IntegrityError,
                t.add, scope=A_SCOPE, uuid='uuid2', name=A_NAME,
            )

    def test_add_with_same_scope_and_uuid_fails(self):
        with self.uuid_translator as t:
            t.add(scope=A_SCOPE, uuid=A_UUID, name='name1')
            self.assertRaises(
                m.IntegrityError,
                t.add, scope=A_SCOPE, uuid=A_UUID, name='name2',
            )

    def test_rename(self):
        with self.uuid_translator as t:
            t.add(scope=A_SCOPE, uuid='uuid1', name='name1')
            t.rename(
                scope=A_SCOPE,
                old_name='name1', new_name='name',
            )
            t.add(scope=A_SCOPE, uuid='uuid2', name='name1')

    def test_rename_fails_if_new_name_already_exists(self):
        with self.uuid_translator as t:
            t.add(scope=A_SCOPE, uuid='uuid1', name='name1')
            t.add(scope=A_SCOPE, uuid='uuid2', name='name2')
            self.assertRaises(
                m.IntegrityError,
                t.rename, scope=A_SCOPE, old_name='name1', new_name='name2',
            )

    def test_same_uuid_and_name_can_exist_under_different_scope(self):
        with self.uuid_translator as t:
            t.add(scope='scope1', uuid=A_UUID, name=A_NAME)
            t.add(scope='scope2', uuid=A_UUID, name=A_NAME)
            self.assertEqual(A_UUID, t.get_uuid(scope='scope1', name=A_NAME))

    def test_persistence(self):
        tmpdir = self.new_temp_dir()

        dbfile1 = os.path.join(tmpdir, 'uuid_names1.sqlite')
        dbfile2 = os.path.join(tmpdir, 'uuid_names2.sqlite')

        with m.uuid_translator(dbfile1) as t:
            t.add(scope=A_SCOPE, uuid='uuid1', name='name1')
            t.rename(
                scope=A_SCOPE,
                old_name='name1', new_name='name',
            )
            t.add(scope=A_SCOPE, uuid='uuid2', name='name1')

        shutil.copy(dbfile1, dbfile2)

        with m.uuid_translator(dbfile2) as t:
            self.assertEqual('name', t.get_name(scope=A_SCOPE, uuid='uuid1'))
            self.assertEqual('name1', t.get_name(scope=A_SCOPE, uuid='uuid2'))
