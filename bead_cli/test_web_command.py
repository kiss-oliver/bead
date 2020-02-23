import re
from bead.tech.fs import read_file, rmtree, write_file
from bead.test import TestCase

from . import test_fixtures as fixtures

from tests.web.test_graphviz import needs_dot


class Test_web(TestCase, fixtures.RobotAndBeads):

    # tests

    def test_dot_output(self, robot, bead_with_inputs):
        robot.cli('web', 'dot', 'web.dot')
        self.assert_file_exists(robot.cwd / 'web.dot')

    @needs_dot
    def test_svg_output(self, robot, bead_with_inputs):
        robot.cli('web', 'svg', 'web.svg')
        self.assert_file_exists(robot.cwd / 'web.svg')

    @needs_dot
    def test_png_output(self, robot, bead_with_inputs):
        robot.cli('web', 'png', 'web.png')
        self.assert_file_exists(robot.cwd / 'web.png')

    def test_meta_save_load(self, robot, bead_with_inputs, box):
        robot.cli('web', 'save', 'all.web')
        self.assert_file_exists(robot.cwd / 'all.web')

        robot.cli('web', 'dot', 'all.dot')
        orig_web_dot = read_file(robot.cwd / 'all.dot')

        assert 'bead_a' in orig_web_dot
        assert 'bead_b' in orig_web_dot
        assert bead_with_inputs in orig_web_dot

        # destroy everything, except the meta files
        write_file(robot.cwd / 'all.dot', '')
        robot.cli('box', 'forget', box.name)
        rmtree(box.directory)

        robot.cli('web', 'load', 'all.web', 'dot', 'web.dot')
        meta_web_dot = read_file(robot.cwd / 'web.dot')

        assert orig_web_dot == meta_web_dot

    def test_heads_only(self, robot, bead_with_history):
        robot.cli('web', 'dot', 'web.dot', 'heads', 'dot', 'heads-only.dot')
        full_web = read_file(robot.cwd / 'web.dot')
        heads_only_web = read_file(robot.cwd / 'heads-only.dot')

        assert len(heads_only_web) < len(full_web)

    def test_invalid_command_reported(self, robot):
        with self.assertRaises(SystemExit):
            robot.cli('web', 'load', 'x', 'this-command-does-not-exist', 'c')
        assert 'ERROR' in robot.stderr
        assert re.search('.ould not .*parse', robot.stderr)
        assert str(['this-command-does-not-exist', 'c']) in robot.stderr
