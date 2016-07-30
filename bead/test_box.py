from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from .test import TestCase
from .box import Box
from .tech.fs import write_file
from .tech.timestamp import time_from_user
from .workspace import Workspace


class Test_box_with_beads(TestCase):

    # fixtures
    def box(self):
        box = Box('test', self.new_temp_dir())

        def add_bead(name, kind, timestamp):
            ws = Workspace(self.new_temp_dir() / name)
            ws.create(kind)
            box.store(ws, timestamp)

        add_bead('bead1', 'test-bead1', '20160704T000000000000+0200')
        add_bead('bead2', 'test-bead2', '20160704T162800000000+0200')
        return box

    # tests
    def test_find_beads(self, box):
        conditions = ()
        self.assertEquals(
            set(['bead1', 'bead2']),
            set(b.name for b in box.find_beads(conditions)))

    def test_find_names(self, box):
        timestamp = time_from_user('20160704T162800000000+0200')
        (
            exact_match, best_guess, best_guess_timestamp, names
        ) = box.find_names(kind='test-bead1', content_id='', timestamp=timestamp)

        self.assertIsNone(exact_match)
        self.assertEquals('bead1', best_guess)
        self.assertIsNotNone(best_guess_timestamp)
        self.assertEquals(set(['bead1']), set(names))


class Test_box_methods_tolerate_junk_in_box(Test_box_with_beads):

    # fixtures
    def box(self):
        box = Test_box_with_beads.box(self)
        # add junk
        write_file(box.directory / 'some-non-bead-file', 'random bits')
        return box
