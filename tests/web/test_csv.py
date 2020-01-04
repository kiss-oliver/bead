import csv
import io

import pytest

from bead_cli.web.csv import read_beads, write_beads, BeadMetaCsvStreams
from bead_cli.web.freshness import Freshness


INPUT_CSV = """\
owner,name,kind,content_id,freeze_time
id_ood1,root,kind_root_1,id_root1_ood,20180321T191922693711+0100

id_ood2,ood1,kind_ood1,id_ood1,20190321T191922693711+0100
id_ood2,root2,kind_root_2,id_root2_utd,20190321T191922693711+0100

id_ood3,ood2,kind_ood2,id_ood2,20190321T191922693711+0100
id_ood3,phantom,kind_ood2,id_phantom,20140321T191922693711+0100

"""

BEAD_CSV = """\
box,name,kind,content_id,freeze_time,freshness

box,ood2,kind_ood2,id_ood2,20190321T191922693711+0100,SUPERSEDED

box,ood1,kind_ood1,id_ood1,20190321T191922693711+0100,UP_TO_DATE

,root2,kind_root_2,id_root2_utd,20190321T191922693711+0100,OUT_OF_DATE

,root1,kind_root_1,id_root1_utd,20190321T191922693711+0100,SUPERSEDED
,root1,kind_root_1,id_root1_ood,20180321T191922693711+0100,SUPERSEDED

,ood3,kind_ood3,id_ood3,20190321T191922693711+0100,UP_TO_DATE
"""

INPUT_MAPS_CSV = """\
box,name,content_id,input,bead_name

box,ood2,id_ood2,root2,root2
box,ood2,id_ood2,ood1,ood1

box,ood1,id_ood1,root,root1

,ood3,id_ood3,phantom,real_name_of_phantom
"""


@pytest.fixture
def test_beads():
    with (
        BeadMetaCsvStreams(
            beads=io.StringIO(BEAD_CSV),
            inputs=io.StringIO(INPUT_CSV),
            input_maps=io.StringIO(INPUT_MAPS_CSV))) as streams:
        return streams.read_beads()


def test_freshness(test_beads):
    beads_by_name = {b.name: b for b in test_beads}
    assert beads_by_name['ood2'].freshness == Freshness.SUPERSEDED
    assert beads_by_name['ood1'].freshness == Freshness.UP_TO_DATE
    assert beads_by_name['root2'].freshness == Freshness.OUT_OF_DATE


def test_written_data_is_unchanged(test_beads):
    streams = (
        BeadMetaCsvStreams(
            beads=io.StringIO(),
            inputs=io.StringIO(),
            input_maps=io.StringIO()))

    streams.write_beads(test_beads)

    def read_sorted(text_csv, fields):
        def sort_key(record):
            return [record[field] for field in fields]
        return sorted(csv.DictReader(io.StringIO(text_csv)), key=sort_key)

    # written beads remain the same
    sort_fields = ['content_id']
    assert (
        read_sorted(BEAD_CSV, sort_fields) ==
        read_sorted(streams.beads.getvalue(), sort_fields))
    # written inputs remain the same
    sort_fields = ['owner', 'content_id']
    assert (
        read_sorted(INPUT_CSV, sort_fields) ==
        read_sorted(streams.inputs.getvalue(), sort_fields))
    # written input_maps remain the same
    sort_fields = ['box', 'name', 'content_id', 'input']
    assert (
        read_sorted(INPUT_MAPS_CSV, sort_fields) ==
        read_sorted(streams.input_maps.getvalue(), sort_fields))


def test_files(tmp_path, test_beads):
    file_base = tmp_path / 'test_'

    write_beads(file_base, test_beads)
    beads_read_back = read_beads(file_base)
    assert test_beads == beads_read_back


def test_missing_file(tmp_path):
    file_base = tmp_path / 'test_'

    with pytest.raises(FileNotFoundError):
        read_beads(file_base)
