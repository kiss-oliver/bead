import re
from bead.tech.fs import read_file, rmtree, write_file
from bead.tech import persistence
from bead.test import TestCase

from bead_cli.web.freshness import Freshness
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
        robot.cli('web load computation.web / .. / save filtered.web')

        assert robot.read_file('computation.web') == robot.read_file('filtered.web')

    def test_filter_sources_through_cluster_links(self, robot, indirect_links_sketch):
        robot.cli('web load computation.web / b .. / save filtered.web')

        sketch = Sketch.from_file(robot.cwd / 'filtered.web')
        assert sketch.cluster_by_name.keys() == set('bcd')
        assert len(sketch.cluster_by_name['c']) == 2

    def test_filter_sinks_through_cluster_links(self, robot, indirect_links_sketch):
        robot.cli('web load computation.web / .. c / save filtered.web')

        sketch = Sketch.from_file(robot.cwd / 'filtered.web')
        assert sketch.cluster_by_name.keys() == set('abc')
        assert len(sketch.cluster_by_name['c']) == 2

    def test_filter(self, robot, sketch):
        robot.cli('web load computation.web / b c .. c f / save filtered.web')
        sketch = Sketch.from_file(robot.cwd / 'filtered.web')
        assert sketch.cluster_by_name.keys() == set('bcef')

    def test_filter_filtered_out_sink(self, robot, indirect_links_sketch):
        # f1 is unreachable from sources {b, c}, so it will be not a reachable sink
        robot.cli('web load computation.web / b c .. c f / save filtered.web')

        sketch = Sketch.from_file(robot.cwd / 'filtered.web')
        assert sketch.cluster_by_name.keys() == set('bc')


class Test_rewire(TestCase, fixtures.RobotAndBeads):
    def renamed_e_web_file(self, robot):
        sketcher = Sketcher()
        sketcher.define('a1 b1 c1 d1 e1 f1')
        sketcher.compile(
            """
            a1 -> b1 -> c1 -> d1
                  b1 ------------> e1 -> f1
            """
        )

        # Mess up the above a bit: make copies of `e1` to `renamed_e` and `another_e_copy`,
        # then deleting `e1`.
        # Since we are just making copies/renaming them, `f1` can use any of them as input.
        # Which one to select of the copies just affects future updates.
        sketcher.phantom('e1')
        sketcher.clone('e1', 'renamed_e')
        sketcher.clone('e1', 'another_e_copy')
        # a1 -> b1 -> c1 -> d1
        #                          [e1] -> f1  # [e1] is phantom - it is not existing by the name e
        #       b1 ------------> renamed_e[e1]
        #       b1 ------------> another_e_copy[e1]

        output_filename = robot.cwd / 'computation.web'
        sketcher.sketch.to_file(output_filename)
        return output_filename

    def test_fixture(self, renamed_e_web_file):
        beads = Sketch.from_file(renamed_e_web_file).beads
        self.assert_e_is_phantom(beads)

    def test_load_save_phantom(self, robot, renamed_e_web_file):
        # this is not a rewire test, but an issue with load come up during writing rewire tests
        # and here we already have the fixture
        robot.cli(f'web load {renamed_e_web_file} save load-save.web')
        beads = Sketch.from_file(robot.cwd / 'load-save.web').beads
        self.assert_e_is_phantom(beads)

    def assert_e_is_phantom(self, beads):
        [e] = [b for b in beads if b.name == 'e']
        assert e.freshness == Freshness.PHANTOM

    def test_autofix(self, robot, renamed_e_web_file):
        robot.cli(f'web load {renamed_e_web_file} auto-rewire color / .. f / save auto.web')

        result = Sketch.from_file(robot.cwd / 'auto.web')

        # f has inputs, which are not phantom
        assert len(result.beads) > 1
        assert all(bead.is_not_phantom for bead in result.beads)
        # we get a WARNING for ambiguity
        assert 'WARNING' in robot.stderr
        # selected either renamed_e or another_e_copy, we do not know
        assert "Selected name '" in robot.stderr

    def test_write_rewire_options_file(self, robot, renamed_e_web_file):
        robot.cli(f'web load {renamed_e_web_file} rewire-options rewire-options.json')

        # rewire_options has only one box
        rewire_options = persistence.loads(robot.read_file('rewire-options.json'))
        assert len(rewire_options) == 1

        # has only one bead in box 'main'
        [bead] = rewire_options['main']
        assert bead['name'] == 'f'

        assert {'renamed_e', 'another_e_copy'} == set(bead['input_map']['e'])
        assert 2 == len(bead['input_map']['e'])

    def remap_e_to_renamed_e_json(self, robot):
        rewire_options = {
            'main': [
                {
                    'name': 'f',
                    'content_id': 'content_id_f1',
                    'freeze_time': '20000106T010000000000+0000',
                    # has two options, we also test, that the first one is selected
                    'input_map': {'e': ['renamed_e', 'another_e_copy']}
                },
                {
                    # this does not exist, but should not cause any problem
                    'name': 'non-existing',
                    'content_id': 'content_id_f1',
                    'freeze_time': '20000106T010000000000+0000',
                    'input_map': {'e': ['renamed_e']}
                }
            ],
            'another-box': [
                {
                    # this does not exist, but should not cause any problem
                    'name': 'whatever',
                    'content_id': 'content_id_f1',
                    'freeze_time': '20000106T010000000000+0000',
                    'input_map': {'e': ['renamed_e']}
                }
            ]
        }
        json_filename = robot.cwd / 'rewire-options.json'
        write_file(json_filename, persistence.dumps(rewire_options))
        return json_filename

    def test_rewire(self, robot, renamed_e_web_file, remap_e_to_renamed_e_json):
        robot.cli(
            f'web load {renamed_e_web_file} rewire {remap_e_to_renamed_e_json} save rewired.web')

        sketch = Sketch.from_file(robot.cwd / 'rewired.web')
        [f] = [b for b in sketch.beads if b.name == 'f']
        assert f.input_map == {'e': 'renamed_e'}, f
        assert 'WARNING' in robot.stderr
        assert "Selected name 'renamed_e'" in robot.stderr
