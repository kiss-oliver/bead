from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase, TempDir
from . import ws as m
import fixtures

import os
import re
from ..pkg.workspace import Workspace
from .. import pkg
from .. import db
from ..translations import add_translation, Peer


class Robot(fixtures.Fixture):
    '''
    Represents a fake user.

    Have a temporary environment with temporary config and working directory.
    '''

    def setUp(self):
        super(Robot, self).setUp()
        self.base_dir = self.useFixture(TempDir()).path

    def cleanUp(self):
        super(Robot, self).cleanUp()
        self.base_dir = None

    @property
    def config_dir(self):
        return self.base_dir / 'config'

    @property
    def home(self):
        return self.base_dir / 'home'

    def ws(self, *args):
        '''
        Imitate calling the ws tool with the given args
        '''
        m.cli(self.config_dir, args)

    def files(self, pattern='.*'):
        return [
            self.base_dir / filename
            for filename in os.listdir(self.base_dir)
            if re.fullmatch(pattern, filename)]


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

    @property
    def personal_id(self):
        return Peer.self().id

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
        m.new('new')

    def when_new_is_called_with_already_existing_name(self):
        self.__stderr = fixtures.StringStream('stderr')
        self.useFixture(self.__stderr)
        self.assertTrue(Peer.self().knows_about('existing'))
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
        self.assertTrue(Peer.self().knows_about('new'))

    def then_workspace_uuid_is_the_uuid_registered_for_name(self):
        self.assertEqual(
            Workspace('new').meta[pkg.metakey.PACKAGE],
            Peer.self().get_translation('new').package_uuid)
