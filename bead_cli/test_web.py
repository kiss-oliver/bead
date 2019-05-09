from collections import defaultdict
import io
import csv

from bead.tech.timestamp import time_from_timestamp

from bead.test import TestCase
from bead.meta import InputSpec
from . import web as m


def _read_csv(text):
    records = list(csv.DictReader(io.StringIO(text)))
    return records


INPUT_CSV = """\
owner,name,kind,content_id,freeze_time
id_ood1,root,kind_root_1,id_root1_ood,20180321T191922693711+0100

id_ood2,ood1,kind_ood1,id_ood1,20190321T191922693711+0100
id_ood2,root2,kind_root_2,id_root2_utd,20190321T191922693711+0100

id_ood3,ood2,kind_ood2,id_ood2,20190321T191922693711+0100
id_ood3,phantom,kind_ood2,id_phantom,20140321T191922693711+0100

"""

BEAD_CSV = """\
name,kind,content_id,freeze_time

ood2,kind_ood2,id_ood2,20190321T191922693711+0100

ood1,kind_ood1,id_ood1,20190321T191922693711+0100

root2,kind_root_2,id_root2_utd,20190321T191922693711+0100

root1,kind_root_1,id_root1_utd,20190321T191922693711+0100
root1,kind_root_1,id_root1_ood,20180321T191922693711+0100

ood3,kind_ood3,id_ood3,20190321T191922693711+0100
"""


def _read_inputs(text):
    inputs_by_owner = defaultdict(list)
    for raw_input in _read_csv(text):
        input = InputSpec(
            raw_input['name'],
            raw_input['kind'],
            raw_input['content_id'],
            raw_input['freeze_time'])
        inputs_by_owner[raw_input['owner']].append(input)
    return dict(inputs_by_owner)


def read_beads(beads_csv, inputs_csv):
    inputs_by_owner = _read_inputs(inputs_csv)
    beads = [
        m.Bead(
            kind=rb['kind'],
            timestamp=time_from_timestamp(rb['freeze_time']),
            content_id=rb['content_id'],
            inputs=inputs_by_owner.get(rb['content_id'], ()),
            name=rb['name'])
        for rb in _read_csv(beads_csv)]
    return beads


class Test_Weaver(TestCase):

    def beads(self):
        return read_beads(BEAD_CSV, INPUT_CSV)

    def weaver(self, beads):
        return m.Weaver(beads)

    def test_phantom_bead(self, weaver):
        # phantom beads are created
        phantom = weaver.content_id_to_bead['id_phantom']
        self.assertEqual('kind_ood2', phantom.kind)
        self.assertEqual('phantom', phantom.name)

    def test_colors(self, weaver):
        def assert_state(content_id, state):
            assert weaver.content_id_to_bead[content_id].state == state

        assert_state('id_root1_ood', m.BeadState.SUPERSEDED)
        assert_state('id_root1_utd', m.BeadState.UP_TO_DATE)
        assert_state('id_root2_utd', m.BeadState.UP_TO_DATE)
        assert_state('id_phantom', m.BeadState.PHANTOM)
        assert_state('id_ood1', m.BeadState.OUT_OF_DATE)
        assert_state('id_ood2', m.BeadState.OUT_OF_DATE)
        assert_state('id_ood3', m.BeadState.OUT_OF_DATE)

    def test_restrict_to(self, weaver):
        # after creation time, we have the whole bead set to plot
        orig_content_ids = set(weaver.content_ids_to_plot)
        self.assertEqual(orig_content_ids, set(weaver.content_id_to_bead))
        # calculating the dependencies of id_ood3, we get almost the whole
        # bead set we will miss only one bead: the updated root1, as no bead
        # depends on it, yet
        weaver.restrict_to({'id_ood3'})
        self.assertEqual(orig_content_ids - {'id_root1_utd'}, weaver.content_ids_to_plot)

    def test_weave(self, weaver):
        # test no exception
        web = weaver.weave()
        assert web.startswith('digraph {\n'), web

    # helper - in context of Weaver
    def test_cluster_by_kind(self, weaver):
        beads_by_kind = m.cluster_by_kind(weaver.all_beads)
        kinds = {
            "kind_ood1", "kind_ood2", "kind_ood3",
            "kind_root_1", "kind_root_2"}
        self.assertEqual(kinds, set(beads_by_kind))

        def content_ids_by_kind(kind):
            return [bead.content_id for bead in beads_by_kind[kind]]

        self.assertEqual(
            ["id_root1_utd", "id_root1_ood"],
            content_ids_by_kind("kind_root_1"))

        self.assertEqual(["id_ood1"], content_ids_by_kind("kind_ood1"))

        self.assertEqual(
            ["id_ood2", "id_phantom"], content_ids_by_kind("kind_ood2"))
