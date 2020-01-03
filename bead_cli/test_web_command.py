from bead.tech.fs import read_file, rmtree, write_file
from bead.test import TestCase

from . import test_fixtures as fixtures

from tests.web.test_graphviz import needs_dot


class Test_web(TestCase, fixtures.RobotAndBeads):

    # tests

    def test_dot_output(self, robot, bead_with_inputs):
        robot.cli('web', 'graph', 'web')
        self.assert_file_exists(robot.cwd / 'web.dot')

    @needs_dot
    def test_svg_output(self, robot, bead_with_inputs):
        robot.cli('web', 'graph', '--svg', 'web')
        self.assert_file_exists(robot.cwd / 'web.svg')

    @needs_dot
    def test_png_output(self, robot, bead_with_inputs):
        robot.cli('web', 'graph', '--png', 'web')
        self.assert_file_exists(robot.cwd / 'web.png')

    def test_csv(self, robot, bead_with_inputs, box):
        robot.cli('web', 'graph', 'web')
        robot.cli('web', 'export', 'web')
        orig_web_dot = read_file(robot.cwd / 'web.dot')

        self.assert_file_exists(robot.cwd / 'web_beads.csv')
        self.assert_file_exists(robot.cwd / 'web_inputs.csv')
        self.assert_file_exists(robot.cwd / 'web_input_maps.csv')

        assert 'bead_a' in orig_web_dot
        assert 'bead_b' in orig_web_dot
        assert bead_with_inputs in orig_web_dot

        # destroy everything, except the csv files
        write_file(robot.cwd / 'web.dot', '')
        robot.cli('box', 'forget', box.name)
        rmtree(box.directory)

        robot.cli('web', 'graph', '--from-csv', 'web')
        csv_web_dot = read_file(robot.cwd / 'web.dot')

        assert orig_web_dot == csv_web_dot

    def test_heads_only(self, robot, bead_with_history):
        robot.cli('web', 'graph', 'web',)
        full_web = read_file(robot.cwd / 'web.dot')

        robot.cli('web', 'graph', 'web', '--heads-only')
        heads_only_web = read_file(robot.cwd / 'web.dot')

        assert len(heads_only_web) < len(full_web)
