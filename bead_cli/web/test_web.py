import csv
import io
import shutil
import subprocess

from bead.test import TestCase, skipUnless
from . import web as m


# TODO: move to test_graphviz.py
def _has_dot():
    if shutil.which('dot') == '/usr/bin/dot':
        try:
            output = subprocess.check_output(['dot', '-V'], stderr=subprocess.STDOUT)
        except subprocess.SubprocessError:
            return False
        return 'graphviz' in output.decode('utf-8').lower()
    return False


HAS_DOT = _has_dot()


def needs_dot(f):
    """
    Decorator to skip tests requiring GraphViz's dot tool.
    """
    return skipUnless(HAS_DOT, "Requires GraphViz's dot tool")(f)
# end of test_graphviz.py


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

,ood3,id_ood3,phantom,real_name_of_phantom
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


def ts(n):
    return f'{int(m.EPOCH_STR[:4]) + n}{m.EPOCH_STR[4:]}'


class Test_Cluster(TestCase):

    def test_empty_cluster(self):
        c = m.Cluster('empty')

        self.assertEqual('empty', c.name)
        self.assertEqual(0, len(c.beads()))

    def bead(self, timestamp_str, is_phantom=False):
        bead = m.MetaBead(
            timestamp_str=timestamp_str,
            kind='test',
            content_id=f'test {timestamp_str}')
        if is_phantom:
            bead.set_state(m.BeadState.PHANTOM)
        return bead

    def test_add_updates_head(self):
        c = m.Cluster('empty')

        p1 = self.bead(ts(1), is_phantom=True)
        p2 = self.bead(ts(2), is_phantom=True)
        p3 = self.bead(ts(3), is_phantom=True)
        b4 = self.bead(ts(4), is_phantom=False)
        p5 = self.bead(ts(5), is_phantom=True)
        b6 = self.bead(ts(6), is_phantom=False)

        # any phantom head is better than the default empty head
        c.add(p2)
        self.assertIs(c.head, p2)
        # older phantoms do not replace newer ones
        c.add(p1)
        self.assertIs(c.head, p2)
        # newer phantoms replace older ones
        c.add(p3)
        self.assertIs(c.head, p3)
        # non phantoms replace phantoms
        c.add(b4)
        self.assertIs(c.head, b4)
        # phantoms do not replace non phantoms
        c.add(p5)
        self.assertIs(c.head, b4)
        # newer beads replace older heads (if both are non-phantoms)
        c.add(b6)
        self.assertIs(c.head, b6)

        self.assertEqual([b6, p5, b4, p3, p2, p1], c.beads())


class Test_BeadWeb(TestCase):

    def beads(self):
        return test_beads()

    def bead_web(self, beads):
        return m.BeadWeb.from_beads(beads)

    def test_phantom_beads_are_created(self, bead_web):
        # print('\n'.join(f'{c.name}: {c.beads()}' for c in bead_web.clusters))
        phantom = bead_web.get_bead(m.BeadID('real_name_of_phantom', 'id_phantom'))
        self.assertEqual('kind_ood2', phantom.kind)
        self.assertEqual('real_name_of_phantom', phantom.name)

    def test_colors(self, bead_web):
        bead_web.color_beads()

        def assert_state(name, content_id, state):
            self.assertEqual(state, bead_web.get_bead(m.BeadID(name, content_id)).state)

        assert_state('root1', 'id_root1_ood', m.BeadState.SUPERSEDED)
        assert_state('root1', 'id_root1_utd', m.BeadState.UP_TO_DATE)
        assert_state('root2', 'id_root2_utd', m.BeadState.UP_TO_DATE)
        assert_state('real_name_of_phantom', 'id_phantom', m.BeadState.PHANTOM)
        assert_state('ood1', 'id_ood1', m.BeadState.OUT_OF_DATE)
        assert_state('ood2', 'id_ood2', m.BeadState.OUT_OF_DATE)
        assert_state('ood3', 'id_ood3', m.BeadState.OUT_OF_DATE)

    def test_restrict_to(self, bead_web):
        # after creation time, we have the whole bead set to plot
        orig_content_ids = set(bead_web.content_ids_to_plot)
        self.assertEqual(orig_content_ids, set(bead_web.content_id_to_bead))
        # calculating the dependencies of id_ood3, we get almost the whole
        # bead set we will miss only one bead: the updated root1, as no bead
        # depends on it, yet
        bead_web.restrict_to({'id_ood3'})
        self.assertEqual(orig_content_ids - {'id_root1_utd'}, bead_web.content_ids_to_plot)

    def test_as_dot(self, bead_web):
        # test no exception
        dot_source = bead_web.as_dot()
        assert dot_source.startswith('digraph {\n'), dot_source

    @needs_dot
    def test_dot(self, bead_web):
        # XXX: test as_dot() / web command
        bead_web.color_beads()
        assert False

    # helper - in context of bead_web
    def test_cluster_beads(self, bead_web):
        bead_clusters = m.cluster_beads(bead_web.all_beads)
        names = {'root1', 'root2', 'ood1', 'ood2', 'ood3', 'phantom'}
        self.assertEqual(names, set(bead_clusters))

        def content_ids_by_name(name):
            return [bead.content_id for bead in bead_clusters[name]]

        self.assertEqual(
            ["id_root1_utd", "id_root1_ood"],
            content_ids_by_name("root1"))

        self.assertEqual(["id_ood1"], content_ids_by_name("ood1"))

        self.assertEqual(["id_ood2"], content_ids_by_name("ood2"))
