from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase, CaptureStdout, CaptureStderr

import os

from .. import commands
from .. import db
from .. import pkg
from ..pkg.workspace import Workspace
from ..translations import add_translation, Peer


class Test_new(TestCase):  # noqa

    def test_first_workspace(self):
        self.given_an_empty_uuid_name_map()
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

    def setUp(self):  # noqa
        super(Test_new, self).setUp()
        # protect user's home directory
        self.home = self.new_temp_home_dir()
        # protect current directory
        self.current_dir = self.new_temp_dir()
        orig_wd = os.getcwd()
        os.chdir(self.current_dir)
        self.addCleanup(os.chdir, orig_wd)

    def given_an_empty_uuid_name_map(self):
        db.connect(db.MEMORY)

    def given_a_non_empty_uuid_name_map(self):
        self.given_an_empty_uuid_name_map()
        add_translation('existing', 'test-uuid')
        self.assertTrue(Peer.self().knows_about('existing'))

    def when_new_is_called_with_nonexisting_name(self):
        with CaptureStdout():
            commands.workspace.new(Workspace('new'))

    def when_new_is_called_with_already_existing_name(self):
        self.assertTrue(Peer.self().knows_about('existing'))
        with CaptureStderr() as stderr:
            try:
                commands.workspace.new(Workspace('existing'))
            except SystemExit:
                self.__error_raised = True
            finally:
                self.__stderr = stderr.text

    def then_error_is_raised(self):
        self.assertTrue(self.__error_raised)
        self.assertIn('ERROR: ', self.__stderr)

    def then_workspace_is_created(self):
        self.assertTrue(Workspace('new').is_valid)

    def then_uuid_map_is_created_with_the_uuid_name_stored_in_it(self):
        self.assertTrue(Peer.self().knows_about('new'))

    def then_workspace_uuid_is_the_uuid_registered_for_name(self):
        self.assertEqual(
            Workspace('new').meta[pkg.meta.PACKAGE],
            Peer.self().get_translation('new').package_uuid)
