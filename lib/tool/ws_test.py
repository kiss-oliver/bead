from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase
from . import ws as m
import fixtures

import os
from .. import tech
uuid_translator = tech.uuid_translator.uuid_translator
from .. import config
from ..pkg.workspace import Workspace
from .. import pkg


A_SCOPE = 'FIXME: personal-uuid'


class Test_new(TestCase):  # noqa

    def test_first_workspace(self):
        self.given_no_uuid_name_map()
        self.when_new_is_called_with_nonexisting_name()
        self.then_uuid_map_is_created_with_the_uuid_name_stored_in_it()

    def test_new_package_name(self):
        self.given_a_non_empty_uuid_name_map()
        self.when_new_is_called_with_nonexisting_name()
        self.then_workspace_is_created()

    def test_existing_package_name(self):
        self.given_a_non_empty_uuid_name_map()
        self.when_new_is_called_with_already_existing_name()
        self.then_error_is_raised()

    def test_created_workspace_has_same_uuid_as_registered_for_name(self):
        self.given_a_non_empty_uuid_name_map()
        self.when_new_is_called_with_nonexisting_name()
        self.then_workspace_uuid_is_the_uuid_registered_for_name()

    # implementation

    __stderr = None
    __error_raised = False
    home = None
    current_dir = None

    @property
    def packages_db_file_name(self):
        return config.get_path(config.PACKAGES_DB_FILE_NAME)

    @property
    def uuid_translator(self):
        return uuid_translator(self.packages_db_file_name)

    def setUp(self):  # noqa
        super(Test_new, self).setUp()
        # protect user's home directory
        self.home = self.new_temp_home_dir()
        # protect current directory
        self.current_dir = self.new_temp_dir()
        orig_wd = os.getcwd()
        os.chdir(self.current_dir)
        self.addCleanup(os.chdir, orig_wd)

    def given_no_uuid_name_map(self):
        pass

    def given_a_non_empty_uuid_name_map(self):
        config.ensure_config_dir()
        with self.uuid_translator as t:
            t.add(scope=A_SCOPE, name='existing', uuid='test-uuid')
            self.assertTrue(t.has_name(scope=A_SCOPE, name='existing'))

    def when_new_is_called_with_nonexisting_name(self):
        m.new('new')

    def when_new_is_called_with_already_existing_name(self):
        self.__stderr = fixtures.StringStream('stderr')
        self.useFixture(self.__stderr)
        with self.uuid_translator as t:
            self.assertTrue(t.has_name(scope=A_SCOPE, name='existing'))
        with fixtures.MonkeyPatch('sys.stderr', self.__stderr.stream):
            try:
                m.new('existing')
            except SystemExit:
                self.__error_raised = True

    def then_error_is_raised(self):
        self.assertTrue(self.__error_raised)
        self.__stderr.stream.seek(0)
        self.assertIn('ERROR: ', self.__stderr.stream.read())

    def then_workspace_is_created(self):
        self.assertTrue(Workspace('new').is_valid)

    def then_uuid_map_is_created_with_the_uuid_name_stored_in_it(self):
        self.assertTrue(os.path.isfile(self.packages_db_file_name))
        with self.uuid_translator as t:
            self.assertTrue(t.has_name(scope=A_SCOPE, name='new'))

    def then_workspace_uuid_is_the_uuid_registered_for_name(self):
        with self.uuid_translator as t:
            self.assertEqual(
                Workspace('new').meta[pkg.metakey.PACKAGE],
                t.get_uuid(A_SCOPE, 'new'))
