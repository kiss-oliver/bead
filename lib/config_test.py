# coding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from .test import TestCase
from . import tech
from . import config as m
import fixtures


class TempHome(object):

    def given_no_XDG_CONFIG_HOME(self):
        self.useFixture(fixtures.EnvironmentVariable(m.XDG_CONFIG_HOME, None))
        self.home = self.new_temp_home_dir()

    def given_XDG_CONFIG_HOME(self):
        self.xdg_config_home = self.new_temp_dir()
        self.useFixture(
            fixtures.EnvironmentVariable(
                m.XDG_CONFIG_HOME,
                self.xdg_config_home
            )
        )


class Test_get_config_dir_path(TestCase, TempHome):

    def test_is_relative_to_xdg_config_home(self):
        self.given_XDG_CONFIG_HOME()

        # FIXME: tech.fs.parent -> Path.parent
        self.assertEqual(
            self.xdg_config_home, tech.fs.parent(m.get_config_dir_path()))

    def test_xdg_config_home_unset_then_is_relative_to_home(self):
        self.given_no_XDG_CONFIG_HOME()
        self.assertEqual(
            self.home / '.config', tech.fs.parent(m.get_config_dir_path()))


class Test_get_path(TestCase, TempHome):

    def test_is_relative_to_config_dir1(self):
        self.given_no_XDG_CONFIG_HOME()
        self.assertEqual(
            m.get_config_dir_path() / 'configfile', m.get_path('configfile'))

    def test_is_relative_to_config_dir2(self):
        self.given_XDG_CONFIG_HOME()
        self.assertEqual(
            m.get_config_dir_path() / 'configfile', m.get_path('configfile'))


class Test_Config(TestCase, TempHome):

    def test_access_by_indexing(self):
        self.given_XDG_CONFIG_HOME()
        with m.Config() as c:
            c['attr1'] = 'value'
            self.assertEqual('value', c['attr1'])

    def test_persistence(self):
        self.given_XDG_CONFIG_HOME()

        with m.Config() as c:
            c['list'] = [1, 'hello config']
            c['unicode_dict'] = {'kéy': 'valué'}

        with m.Config() as c:
            self.assertEqual([1, 'hello config'], c['list'])
            self.assertEqual({'kéy': 'valué'}, c['unicode_dict'])

    def test_unchanged_config_is_not_persisted(self):
        self.given_XDG_CONFIG_HOME()
        with m.Config() as c:
            c['overwritten'] = False

        with m.Config() as c:
            # overwrite config without Config() knowing about it
            tech.fs.write_file(
                m.get_path(m.CONFIG_FILE_NAME),
                '{"overwritten": true}'
            )
            c['overwritten'] = False

        # we expect that exiting from the with block above, the config
        # is not persisted as it saw no modification to its values since loaded
        with m.Config() as c:
            self.assertTrue(c['overwritten'])
