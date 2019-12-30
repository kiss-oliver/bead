from bead.test import TestCase

import os
from bead.workspace import Workspace
from . import test_fixtures as fixtures


class Test_input_commands(TestCase, fixtures.RobotAndBeads):

    # tests
    def test_basic_usage(self, robot, bead_with_history):
        # nextbead with input1 as databead1
        robot.cli('new', 'nextbead')
        robot.cd('nextbead')
        # add version TS2
        robot.cli('input', 'add', 'input1', 'bead_with_history', '--time', fixtures.TS2)
        self.assert_loaded(robot, 'input1', fixtures.TS2)
        robot.cli('save')
        robot.cd('..')
        robot.cli('nuke', 'nextbead')

        robot.cli('develop', 'nextbead')
        robot.cd('nextbead')
        assert not os.path.exists(robot.cwd / 'input/input1')

        robot.cli('input', 'load')
        assert os.path.exists(robot.cwd / 'input/input1')

        robot.cli('input', 'add', 'input2', 'bead_with_history')
        assert os.path.exists(robot.cwd / 'input/input2')

        robot.cli('input', 'delete', 'input1')
        assert not os.path.exists(robot.cwd / 'input/input1')

        # no-op load do not crash
        robot.cli('input', 'load')

        robot.cli('status')

    def test_update_unloaded_input_w_another_bead(self, robot, bead_with_inputs, bead_a, bead_b):
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)

        robot.cli('status')
        assert bead_b in robot.stdout

        assert not Workspace(robot.cwd).is_loaded('input_b')

        robot.cli('input', 'update', 'input_b', bead_a)
        self.assert_loaded(robot, 'input_b', bead_a)

        robot.cli('status')
        assert bead_b not in robot.stdout

    def test_load_on_workspace_without_input_gives_feedback(self, robot, bead_a):
        robot.cli('develop', bead_a)
        robot.cd(bead_a)
        robot.cli('input', 'load')

        assert 'WARNING' in robot.stderr
        assert 'No inputs defined to load.' in robot.stderr

    def test_load_with_missing_bead_gives_warning(self, robot, bead_with_inputs, bead_a):
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)
        robot.reset()
        robot.cli('input', 'load')
        assert 'WARNING' in robot.stderr
        assert 'input_a' in robot.stderr
        assert 'input_b' in robot.stderr

    def test_load_only_one_input(self, robot, bead_with_inputs, bead_a):
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)
        robot.cli('input', 'load', 'input_a')
        self.assert_loaded(robot, 'input_a', bead_a)
        with robot.environment:
            assert not Workspace('.').is_loaded('input_b')

    def test_deleted_box_does_not_stop_load(self, robot, bead_with_inputs):
        deleted_box = self.new_temp_dir()
        robot.cli('box', 'add', 'missing', deleted_box)
        os.rmdir(deleted_box)
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)
        robot.cli('input', 'load')

    def test_add_with_unrecognized_bead_name_exits_with_error(self, robot, bead_a):
        robot.cli('develop', bead_a)
        robot.cd(bead_a)
        try:
            robot.cli('input', 'add', 'x', 'non-existing-bead')
            self.fail('Expected an error exit!')
        except SystemExit:
            assert 'ERROR' in robot.stderr
            assert 'non-existing-bead' in robot.stderr

    def test_add_with_path_separator_in_name_is_error(self, robot, bead_a, bead_b):
        robot.cli('develop', bead_a)
        robot.cd(bead_a)
        try:
            robot.cli('input', 'add', 'name/with/path/separator', bead_b)
            self.fail('Expected an error exit!')
        except SystemExit:
            assert 'ERROR' in robot.stderr
            assert 'name/with/path/separator' in robot.stderr

            robot.cli('status')
            assert bead_b not in robot.stdout
            self.assertEquals([], list(robot.ls('input')))

    def test_add_with_hacked_bead_is_refused(self, robot, hacked_bead, bead_a):
        robot.cli('develop', bead_a)
        robot.cd(bead_a)
        robot.cli('input', 'add', 'hack', hacked_bead)
        assert not Workspace(robot.cwd).has_input('hack')
        assert 'WARNING' in robot.stderr

    def test_update_with_hacked_bead_is_refused(self, robot, hacked_bead, bead_a):
        robot.cli('develop', bead_a)
        robot.cd(bead_a)
        robot.cli('input', 'add', 'intelligence', bead_a)
        robot.cli('input', 'update', 'intelligence', hacked_bead)
        self.assert_loaded(robot, 'intelligence', bead_a)
        assert 'WARNING' in robot.stderr

    def test_update_to_next_version(self, robot, bead_with_history):
        robot.cli('new', 'test-workspace')
        robot.cd('test-workspace')
        # add version TS1
        robot.cli('input', 'add', 'input1', 'bead_with_history', '--time', fixtures.TS1)
        self.assert_loaded(robot, 'input1', fixtures.TS1)

        robot.cli('input', 'update', 'input1', '--next')
        self.assert_loaded(robot, 'input1', fixtures.TS2)

        robot.cli('input', 'update', 'input1', '-N')
        self.assert_loaded(robot, 'input1', fixtures.TS3)

    def test_update_to_previous_version(self, robot, bead_with_history):
        robot.cli('new', 'test-workspace')
        robot.cd('test-workspace')
        # add version TS1
        robot.cli('input', 'add', 'input1', 'bead_with_history', '--time', fixtures.TS4)
        self.assert_loaded(robot, 'input1', fixtures.TS4)

        robot.cli('input', 'update', 'input1', '--prev')
        self.assert_loaded(robot, 'input1', fixtures.TS3)

        robot.cli('input', 'update', 'input1', '-P')
        self.assert_loaded(robot, 'input1', fixtures.TS2)

    def test_update_up_to_date_inputs_is_noop(self, robot, bead_a, bead_b):
        robot.cli('new', 'test-workspace')
        robot.cd('test-workspace')
        robot.cli('input', 'add', bead_a)
        robot.cli('input', 'add', bead_b)

        def files_with_times():
            basepath = robot.cwd
            for dirpath, dirs, files in os.walk(basepath):
                for file in files:
                    filename = os.path.join(dirpath, file)
                    yield filename, os.path.getctime(filename)

        orig_files = sorted(files_with_times())
        robot.cli('input', 'update')
        after_update_files = sorted(files_with_times())
        self.assertEquals(orig_files, after_update_files)

        assert f'Skipping update of {bead_a}:' in robot.stdout
        assert f'Skipping update of {bead_b}:' in robot.stdout

    def test_update_with_same_bead_is_noop(self, robot, bead_a):
        robot.cli('new', 'test-workspace')
        robot.cd('test-workspace')
        robot.cli('input', 'add', bead_a)

        def files_with_times():
            basepath = robot.cwd
            for dirpath, dirs, files in os.walk(basepath):
                for file in files:
                    filename = os.path.join(dirpath, file)
                    yield filename, os.path.getctime(filename)

        orig_files = sorted(files_with_times())
        robot.cli('input', 'update', bead_a)
        after_update_files = sorted(files_with_times())
        self.assertEquals(orig_files, after_update_files)

        assert f'Skipping update of {bead_a}:' in robot.stdout

    def test_unload_all(self, robot, bead_with_inputs):
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)
        robot.cli('input', 'load')
        assert os.path.exists(robot.cwd / 'input/input_a')
        assert os.path.exists(robot.cwd / 'input/input_b')

        robot.cli('input', 'unload')
        assert not os.path.exists(robot.cwd / 'input/input_a')
        assert not os.path.exists(robot.cwd / 'input/input_b')

    def test_unload(self, robot, bead_with_inputs):
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)
        robot.cli('input', 'load')
        assert os.path.exists(robot.cwd / 'input/input_a')
        assert os.path.exists(robot.cwd / 'input/input_b')

        robot.cli('input', 'unload', 'input_a')
        assert not os.path.exists(robot.cwd / 'input/input_a')
        assert os.path.exists(robot.cwd / 'input/input_b')

        robot.cli('input', 'unload', 'input_b')
        assert not os.path.exists(robot.cwd / 'input/input_a')
        assert not os.path.exists(robot.cwd / 'input/input_b')

        robot.cli('input', 'unload', 'input_a')
        assert not os.path.exists(robot.cwd / 'input/input_a')
        assert not os.path.exists(robot.cwd / 'input/input_b')
