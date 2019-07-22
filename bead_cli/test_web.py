import csv
import io

from bead.test import TestCase
from . import web as m


INPUT_CSV = """\
owner,name,kind,content_id,freeze_time
id_ood1,root,kind_root_1,id_root1_ood,20180321T191922693711+0100

id_ood2,ood1,kind_ood1,id_ood1,20190321T191922693711+0100
id_ood2,root2,kind_root_2,id_root2_utd,20190321T191922693711+0100

id_ood3,ood2,kind_ood2,id_ood2,20190321T191922693711+0100
id_ood3,phantom,kind_ood2,id_phantom,20140321T191922693711+0100

"""

BEAD_CSV = """\
box,name,kind,content_id,freeze_time

box,ood2,kind_ood2,id_ood2,20190321T191922693711+0100

box,ood1,kind_ood1,id_ood1,20190321T191922693711+0100

,root2,kind_root_2,id_root2_utd,20190321T191922693711+0100

,root1,kind_root_1,id_root1_utd,20190321T191922693711+0100
,root1,kind_root_1,id_root1_ood,20180321T191922693711+0100

,ood3,kind_ood3,id_ood3,20190321T191922693711+0100
"""

INPUT_MAPS_CSV = """\
box,name,content_id,input,bead_name

box,ood2,id_ood2,root2,root2
box,ood2,id_ood2,ood1,ood1

box,ood1,id_ood1,root,root1
"""


def test_beads():
    return m.read_beads(
        io.StringIO(BEAD_CSV),
        io.StringIO(INPUT_CSV),
        io.StringIO(INPUT_MAPS_CSV))


class Test_bead_csv_io(TestCase):
    def test_written_data_is_unchanged(self):
        beads = test_beads()
        beads_csv_stream = io.StringIO()
        inputs_csv_stream = io.StringIO()
        input_maps_csv_stream = io.StringIO()
        m.write_beads(beads, beads_csv_stream, inputs_csv_stream, input_maps_csv_stream)

        def read_sorted(text_csv, fields):
            def sort_key(record):
                return [record[field] for field in fields]
            return sorted(csv.DictReader(io.StringIO(text_csv)), key=sort_key)

        # written beads remain the same
        sort_fields = ['content_id']
        self.assertEqual(
            read_sorted(BEAD_CSV, sort_fields),
            read_sorted(beads_csv_stream.getvalue(), sort_fields))
        # written inputs remain the same
        sort_fields = ['owner', 'content_id']
        self.assertEqual(
            read_sorted(INPUT_CSV, sort_fields),
            read_sorted(inputs_csv_stream.getvalue(), sort_fields))
        # written input_maps remain the same
        sort_fields = ['box', 'name', 'content_id', 'input']
        self.assertEqual(
            read_sorted(INPUT_MAPS_CSV, sort_fields),
            read_sorted(input_maps_csv_stream.getvalue(), sort_fields))


class Test_Weaver(TestCase):

    def beads(self):
        return test_beads()

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
        web = weaver.weave(do_all_edges=True)
        assert web.startswith('digraph {\n'), web

    # helper - in context of Weaver
    def test_cluster_beads(self, weaver):
        bead_clusters = m.cluster_beads(weaver.all_beads)
        names = {'root1', 'root2', 'ood1', 'ood2', 'ood3', 'phantom'}
        self.assertEqual(names, set(bead_clusters))

        def content_ids_by_name(name):
            return [bead.content_id for bead in bead_clusters[name]]

        self.assertEqual(
            ["id_root1_utd", "id_root1_ood"],
            content_ids_by_name("root1"))

        self.assertEqual(["id_ood1"], content_ids_by_name("ood1"))

        self.assertEqual(["id_ood2"], content_ids_by_name("ood2"))
