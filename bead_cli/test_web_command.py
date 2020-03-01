import re
from bead.tech.fs import read_file, rmtree, write_file
from bead.test import TestCase

from bead_cli.web.sketch import Sketch
from . import test_fixtures as fixtures
from tests.sketcher import Sketcher
from tests.web.test_graphviz import needs_dot


class Test_web(TestCase, fixtures.RobotAndBeads):

    # tests

    def test_dot_output(self, robot, bead_with_inputs):
        robot.cli('web dot all.dot')
        self.assert_file_exists(robot.cwd / 'all.dot')

    @needs_dot
    def test_svg_output(self, robot, bead_with_inputs):
        robot.cli('web svg all.svg')
        self.assert_file_exists(robot.cwd / 'all.svg')

    @needs_dot
    def test_png_output(self, robot, bead_with_inputs):
        robot.cli('web png all.png')
        self.assert_file_exists(robot.cwd / 'all.png')

    def test_meta_save_load(self, robot, bead_with_inputs, box):
        robot.cli('web save all.web')
        self.assert_file_exists(robot.cwd / 'all.web')

        robot.cli('web dot all.dot')
        orig_web_dot = read_file(robot.cwd / 'all.dot')

        assert 'bead_a' in orig_web_dot
        assert 'bead_b' in orig_web_dot
        assert bead_with_inputs in orig_web_dot

        # destroy everything, except the meta files
        write_file(robot.cwd / 'all.dot', '')
        robot.cli('box', 'forget', box.name)
        rmtree(box.directory)

        robot.cli('web load all.web dot all.dot')
        meta_web_dot = read_file(robot.cwd / 'all.dot')

        assert orig_web_dot == meta_web_dot

    def test_heads_only(self, robot, bead_with_history):
        robot.cli('web dot all.dot heads dot heads-only.dot')
        full_web = read_file(robot.cwd / 'all.dot')
        heads_only_web = read_file(robot.cwd / 'heads-only.dot')

        assert len(heads_only_web) < len(full_web)

    def test_invalid_command_reported(self, robot):
        with self.assertRaises(SystemExit):
            robot.cli('web load x this-command-does-not-exist c')
        assert 'ERROR' in robot.stderr
        assert re.search('.ould not .*parse', robot.stderr)
        assert str(['this-command-does-not-exist', 'c']) in robot.stderr


class Test_web_filter(TestCase, fixtures.RobotAndBeads):

    def sketch(self, robot):
        sketcher = Sketcher()
        sketcher.define('a1 b1 c1 d1 e1 f1')
        sketcher.compile(
            """
            a1 -> b1 -> c1 -> d1

                  b1 ------------> e1 -> f1
            """
        )
        sketcher.sketch.to_file(robot.cwd / 'computation.web')

    def indirect_links_sketch(self, robot):
        sketcher = Sketcher()
        sketcher.define('a1 b1 b2 c1 c2 d3 e1 f1')
        sketcher.compile(
            """
            a1 -> b1               e1 -> f1
                  b2 -> c1
                        c2 -> d3
            """
        )
        sketcher.sketch.to_file(robot.cwd / 'computation.web')

    def test_filter_no_args_no_filtering(self, robot, sketch):
        robot.cli('web load computation.web / ... / save filtered.web')

        assert robot.read_file('computation.web') == robot.read_file('filtered.web')

    def test_filter_sources_through_cluster_links(self, robot, indirect_links_sketch):
        robot.cli('web load computation.web / b ... / save filtered.web')

        sketch = Sketch.from_file(robot.cwd / 'filtered.web')
        assert sketch.cluster_by_name.keys() == set('bcd')
        assert len(sketch.cluster_by_name['c']) == 2

    def test_filter_sinks_through_cluster_links(self, robot, indirect_links_sketch):
        robot.cli('web load computation.web / ... c / save filtered.web')

        sketch = Sketch.from_file(robot.cwd / 'filtered.web')
        assert sketch.cluster_by_name.keys() == set('abc')
        assert len(sketch.cluster_by_name['c']) == 2

    def test_filter(self, robot, sketch):
        robot.cli('web load computation.web / b c ... c f / save filtered.web')
        sketch = Sketch.from_file(robot.cwd / 'filtered.web')
        assert sketch.cluster_by_name.keys() == set('bcef')

    def test_filter_filtered_out_sink(self, robot, indirect_links_sketch):
        # f1 is unreachable from sources {b, c}, so it will be not a reachable sink
        robot.cli('web load computation.web / b c ... c f / save filtered.web')

        sketch = Sketch.from_file(robot.cwd / 'filtered.web')
        assert sketch.cluster_by_name.keys() == set('bc')
