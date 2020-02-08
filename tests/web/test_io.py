import pytest

from bead_cli.web.io import loads, read_beads, write_beads
from bead_cli.web.freshness import Freshness


META_JSON = """\
[
    {
        "@class": "Dummy",
        "@encoding": "attrs",
        "box_name": "box",
        "content_id": "id_ood2",
        "freshness": {
            "@class": "Freshness",
            "@encoding": "enum",
            "@value": "SUPERSEDED"
        },
        "input_map": {
            "ood1": "ood1",
            "root2": "root2"
        },
        "inputs": [
            {
                "@class": "InputSpec",
                "@encoding": "attrs",
                "content_id": "id_ood1",
                "kind": "kind_ood1",
                "name": "ood1",
                "timestamp_str": "20190321T191922693711+0100"
            },
            {
                "@class": "InputSpec",
                "@encoding": "attrs",
                "content_id": "id_root2_utd",
                "kind": "kind_root_2",
                "name": "root2",
                "timestamp_str": "20190321T191922693711+0100"
            }
        ],
        "kind": "kind_ood2",
        "name": "ood2",
        "timestamp_str": "20190321T191922693711+0100"
    },
    {
        "@class": "Dummy",
        "@encoding": "attrs",
        "box_name": "box",
        "content_id": "id_ood1",
        "freshness": {
            "@class": "Freshness",
            "@encoding": "enum",
            "@value": "UP_TO_DATE"
        },
        "input_map": {
            "root": "root1"
        },
        "inputs": [
            {
                "@class": "InputSpec",
                "@encoding": "attrs",
                "content_id": "id_root1_ood",
                "kind": "kind_root_1",
                "name": "root",
                "timestamp_str": "20180321T191922693711+0100"
            }
        ],
        "kind": "kind_ood1",
        "name": "ood1",
        "timestamp_str": "20190321T191922693711+0100"
    },
    {
        "@class": "Dummy",
        "@encoding": "attrs",
        "box_name": "",
        "content_id": "id_root2_utd",
        "freshness": {
            "@class": "Freshness",
            "@encoding": "enum",
            "@value": "OUT_OF_DATE"
        },
        "input_map": {},
        "inputs": [],
        "kind": "kind_root_2",
        "name": "root2",
        "timestamp_str": "20190321T191922693711+0100"
    },
    {
        "@class": "Dummy",
        "@encoding": "attrs",
        "box_name": "",
        "content_id": "id_root1_utd",
        "freshness": {
            "@class": "Freshness",
            "@encoding": "enum",
            "@value": "SUPERSEDED"
        },
        "input_map": {},
        "inputs": [],
        "kind": "kind_root_1",
        "name": "root1",
        "timestamp_str": "20190321T191922693711+0100"
    },
    {
        "@class": "Dummy",
        "@encoding": "attrs",
        "box_name": "",
        "content_id": "id_root1_ood",
        "freshness": {
            "@class": "Freshness",
            "@encoding": "enum",
            "@value": "SUPERSEDED"
        },
        "input_map": {},
        "inputs": [],
        "kind": "kind_root_1",
        "name": "root1",
        "timestamp_str": "20180321T191922693711+0100"
    },
    {
        "@class": "Dummy",
        "@encoding": "attrs",
        "box_name": "",
        "content_id": "id_ood3",
        "freshness": {
            "@class": "Freshness",
            "@encoding": "enum",
            "@value": "UP_TO_DATE"
        },
        "input_map": {
            "phantom": "real_name_of_phantom"
        },
        "inputs": [
            {
                "@class": "InputSpec",
                "@encoding": "attrs",
                "content_id": "id_ood2",
                "kind": "kind_ood2",
                "name": "ood2",
                "timestamp_str": "20190321T191922693711+0100"
            },
            {
                "@class": "InputSpec",
                "@encoding": "attrs",
                "content_id": "id_phantom",
                "kind": "kind_ood2",
                "name": "phantom",
                "timestamp_str": "20140321T191922693711+0100"
            }
        ],
        "kind": "kind_ood3",
        "name": "ood3",
        "timestamp_str": "20190321T191922693711+0100"
    }
]
"""


def test_freshness():
    test_beads = loads(META_JSON)

    beads_by_name = {b.name: b for b in test_beads}
    assert beads_by_name['ood2'].freshness == Freshness.SUPERSEDED
    assert beads_by_name['ood1'].freshness == Freshness.UP_TO_DATE
    assert beads_by_name['root2'].freshness == Freshness.OUT_OF_DATE


def test_written_data_is_unchanged(tmp_path):
    new_meta = tmp_path / 'new_meta'
    write_beads(new_meta, loads(META_JSON))

    assert new_meta.read_text().splitlines() == META_JSON.splitlines()


def test_files(tmp_path):
    meta = tmp_path / 'new_meta'

    test_beads = loads(META_JSON)
    write_beads(meta, test_beads)
    beads_read_back = read_beads(meta)
    assert test_beads == beads_read_back


def test_missing_file(tmp_path):
    meta = tmp_path / 'nonexisting_file'

    with pytest.raises(FileNotFoundError):
        read_beads(meta)
