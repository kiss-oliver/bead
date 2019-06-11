from bead.test import TestCase, skip

from testtools.matchers import Contains

import shutil
# from bead.workspace import Workspace
from . import test_fixtures as fixtures


class Test_feature_update_by_name(TestCase, fixtures.RobotAndBeads):

    # tests
    def test_basic_support(self, robot, bead_a, bead_with_history, box):
        """
        update by name not by kind
        """
        # (bead_with_history has 5 beads sharing the same name, kind)

        cd = robot.cd
        cli = robot.cli
        branch1 = 'branch1'
        branch2 = 'branch2'
        branch3 = 'branch3'

        def copy(timestamp, new_name):
            _copy(box, bead_with_history, timestamp, new_name)

        # verify, that `add`, `save`, `develop`, `update`, and `status` all work with input_map

        copy(fixtures.TS1, branch1)
        copy(fixtures.TS2, branch2)

        # setup - bead_a with 2 inputs
        cli('develop', bead_a)
        cd(bead_a)
        cli('input', 'add', 'input1', branch1)
        cli('input', 'add', 'input2', branch2)
        self.assert_loaded(robot, 'input1', fixtures.TS1)
        self.assert_loaded(robot, 'input2', fixtures.TS2)

        cli('status')
        self.assertThat(robot.stdout, Contains(f'Branch name: {branch1}'))
        self.assertThat(robot.stdout, Contains(f'Branch name: {branch2}'))

        # `update` works by name, not by kind
        copy(fixtures.TS3, branch1)
        cli('input', 'update')
        self.assert_loaded(robot, 'input1', fixtures.TS3)
        self.assert_loaded(robot, 'input2', fixtures.TS2)

        # save & develop works with names
        cli('save')
        cd('..')
        cli('nuke', bead_a)
        cli('develop', bead_a)
        cd(bead_a)
        copy(fixtures.TS4, branch1)
        copy(fixtures.TS3, branch2)
        cli('input', 'update')
        self.assert_loaded(robot, 'input1', fixtures.TS4)
        self.assert_loaded(robot, 'input2', fixtures.TS3)

        # `update` also sets the branch name
        copy(fixtures.TS1, branch3)
        cli('input', 'update', 'input2', branch3)
        self.assert_loaded(robot, 'input2', fixtures.TS1)
        copy(fixtures.TS4, branch3)
        cli('input', 'update', 'input2')
        self.assert_loaded(robot, 'input1', fixtures.TS4)
        self.assert_loaded(robot, 'input2', fixtures.TS4)

    @skip('unimplemented')
    def test_load_does_not_find_renamed_bead(self):
        # reason: speed
        # reason: implementation simplicity
        pass

    @skip('unimplemented')
    def test_locate(self):
        # new command, that finds renamed beads by kind or by content_id
        #  - to be used for fixing branch names
        pass


def _copy(box, bead_name, bead_timestamp, new_name):
    """
    Copy a bead to a new name within box.
    """
    # FIXME: this test helper uses private implementation information
    source = box.directory / f'{bead_name}_{bead_timestamp}.zip'
    destination = box.directory / f'{new_name}_{bead_timestamp}.zip'
    shutil.copy(source, destination)
