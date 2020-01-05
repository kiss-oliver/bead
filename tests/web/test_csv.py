import csv
import io
from zipfile import ZipFile
import pytest

from bead_cli.web.csv import read_beads, write_beads
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
def test_beads(tmp_path):
    meta = tmp_path / 'temp_meta'

    with ZipFile(meta, 'w') as zf:
        zf.writestr('beads.csv', BEAD_CSV)
        zf.writestr('inputs.csv', INPUT_CSV)
        zf.writestr('input_maps.csv', INPUT_MAPS_CSV)

    return read_beads(meta)


def test_freshness(test_beads):
    beads_by_name = {b.name: b for b in test_beads}
    assert beads_by_name['ood2'].freshness == Freshness.SUPERSEDED
    assert beads_by_name['ood1'].freshness == Freshness.UP_TO_DATE
    assert beads_by_name['root2'].freshness == Freshness.OUT_OF_DATE


def test_written_data_is_unchanged(test_beads, tmp_path):
    new_meta = tmp_path / 'new_meta'
    write_beads(new_meta, test_beads)

    def read_sorted(text_csv, fields):
        def sort_key(record):
            return [record[field] for field in fields]
        return sorted(csv.DictReader(io.StringIO(text_csv)), key=sort_key)

    def read_zip(filename):
        with ZipFile(new_meta) as zf:
            with zf.open(filename) as f:
                return io.TextIOWrapper(f).read()

    # written beads remain the same
    sort_fields = ['content_id']
    assert (
        read_sorted(BEAD_CSV, sort_fields) ==
        read_sorted(read_zip('beads.csv'), sort_fields))
    # written inputs remain the same
    sort_fields = ['owner', 'content_id']
    assert (
        read_sorted(INPUT_CSV, sort_fields) ==
        read_sorted(read_zip('inputs.csv'), sort_fields))
    # written input_maps remain the same
    sort_fields = ['box', 'name', 'content_id', 'input']
    assert (
        read_sorted(INPUT_MAPS_CSV, sort_fields) ==
        read_sorted(read_zip('input_maps.csv'), sort_fields))


def test_files(tmp_path, test_beads):
    meta = tmp_path / 'new_meta'

    write_beads(meta, test_beads)
    beads_read_back = read_beads(meta)
    assert test_beads == beads_read_back


def test_missing_file(tmp_path):
    meta = tmp_path / 'nonexisting_file'

    with pytest.raises(FileNotFoundError):
        read_beads(meta)
