# coding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from .test import TestCase
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

        self.assertEqual(
            self.xdg_config_home, m.get_config_dir_path().parent)

    def test_xdg_config_home_unset_then_is_relative_to_home(self):
        self.given_no_XDG_CONFIG_HOME()
        self.assertEqual(
            self.home / '.config', m.get_config_dir_path().parent)


class Test_get_path(TestCase, TempHome):

    def test_is_relative_to_config_dir1(self):
        self.given_no_XDG_CONFIG_HOME()
        self.assertEqual(
            m.get_config_dir_path() / 'configfile', m.get_path('configfile'))

    def test_is_relative_to_config_dir2(self):
        self.given_XDG_CONFIG_HOME()
        self.assertEqual(
            m.get_config_dir_path() / 'configfile', m.get_path('configfile'))


class Test_persistence(TestCase, TempHome):

    def test_persistence(self):
        self.given_a_valid_config_directory()

        c = m.load()
        c['list'] = [1, 'hello config']
        c['unicode_dict'] = {'kéy': 'valué'}
        m.save(c)

        c = m.load()
        self.assertEqual([1, 'hello config'], c['list'])
        self.assertEqual({'kéy': 'valué'}, c['unicode_dict'])

    def test_personal_id(self):
        self.given_a_valid_config_directory()

        id1 = m.get_personal_id()

        id2 = m.get_personal_id()
        self.assertEqual(id1, id2)

    def given_a_valid_config_directory(self):
        self.given_XDG_CONFIG_HOME()
        m.ensure_config_dir()
