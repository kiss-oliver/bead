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
        self.config = m.Config()

    def given_XDG_CONFIG_HOME(self):
        self.xdg_config_home = self.new_temp_dir()
        self.useFixture(
            fixtures.EnvironmentVariable(
                m.XDG_CONFIG_HOME,
                self.xdg_config_home
            )
        )
        self.config = m.Config()


class Test_root(TestCase, TempHome):

    def test_is_relative_to_xdg_config_home(self):
        self.given_XDG_CONFIG_HOME()
        self.assertEqual(self.xdg_config_home, self.config.root.parent)

    def test_xdg_config_home_unset_then_is_relative_to_home(self):
        self.given_no_XDG_CONFIG_HOME()
        self.assertEqual(self.home / '.config', self.config.root.parent)


class Test_path_to(TestCase, TempHome):

    def test_is_relative_to_config_dir1(self):
        self.given_no_XDG_CONFIG_HOME()

        self.assertEqual(
            self.config.root / 'configfile', self.config.path_to('configfile'))

    def test_is_relative_to_config_dir2(self):
        self.given_XDG_CONFIG_HOME()
        self.assertEqual(
            self.config.root / 'configfile', self.config.path_to('configfile'))


class Test_persistence(TestCase, TempHome):

    def test_newly_created_config(self):
        self.given_a_valid_config_directory()

        # load & check
        cfg = m.Config()
        self.assertEqual([], cfg.repositories)
        self.assertIsNone(cfg.default_store_repository)

    def test_persistence(self):
        self.given_a_valid_config_directory()

        cfg = m.Config()
        cfg.repositories.append('/repo1')
        cfg.repositories.append('/repo2')
        cfg.default_store_repository = '/repo3'
        c = cfg.config
        c['list'] = [1, 'hello config']
        c['unicode_dict'] = {'kéy': 'valué'}
        cfg.save()

        cfg = m.Config()
        self.assertEqual(['/repo1', '/repo2'], cfg.repositories)
        self.assertEqual('/repo3', cfg.default_store_repository)
        c = m.Config().config
        self.assertEqual([1, 'hello config'], c['list'])
        self.assertEqual({'kéy': 'valué'}, c['unicode_dict'])

    def test_personal_id(self):
        self.given_a_valid_config_directory()

        id1 = m.Config().personal_id

        id2 = m.Config().personal_id
        self.assertEqual(id1, id2)

    def given_a_valid_config_directory(self):
        self.given_XDG_CONFIG_HOME()
