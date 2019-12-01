from bead.tech.fs import read_file, rmtree, write_file
from bead.test import TestCase
from testtools.matchers import FileExists

from . import test_fixtures as fixtures

from tests.web.test_graphviz import needs_dot


class Test_web(TestCase, fixtures.RobotAndBeads):

    # tests

    def test_dot_output(self, robot, bead_with_inputs):
        robot.cli('web', '-o', 'web')
        self.assertThat(robot.cwd / 'web.dot', FileExists())

    @needs_dot
    def test_svg_output(self, robot, bead_with_inputs):
        robot.cli('web', '--svg', '-o', 'web')
        self.assertThat(robot.cwd / 'web.svg', FileExists())

    @needs_dot
    def test_png_output(self, robot, bead_with_inputs):
        robot.cli('web', '--png', '-o', 'web')
        self.assertThat(robot.cwd / 'web.png', FileExists())

    def test_csv(self, robot, bead_with_inputs, box):
        robot.cli('web', '--to-csv', '-o', 'web')
        orig_web_dot = read_file(robot.cwd / 'web.dot')

        self.assertThat(robot.cwd / 'web_beads.csv', FileExists())
        self.assertThat(robot.cwd / 'web_inputs.csv', FileExists())
        self.assertThat(robot.cwd / 'web_input_maps.csv', FileExists())

        assert 'bead_a' in orig_web_dot
        assert 'bead_b' in orig_web_dot
        assert bead_with_inputs in orig_web_dot

        # destroy everything, except the csv files
        write_file(robot.cwd / 'web.dot', '')
        robot.cli('box', 'forget', box.name)
        rmtree(box.directory)

        robot.cli('web', '--from-csv', 'web')
        csv_web_dot = read_file(robot.cwd / 'web.dot')

        assert orig_web_dot == csv_web_dot

    def test_heads_only(self, robot, bead_with_history):
        robot.cli('web', '-o', 'web',)
        full_web = read_file(robot.cwd / 'web.dot')

        robot.cli('web', '-o', 'web', '--heads-only')
        heads_only_web = read_file(robot.cwd / 'web.dot')

        assert len(heads_only_web) < len(full_web)
