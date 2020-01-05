import csv
import io
from zipfile import ZipFile
from collections import defaultdict
from typing import List

import attr

from bead.meta import InputSpec
from .dummy import Dummy, Freshness


def write_beads(file_name, beads: List[Dummy]):
    with ZipFile(file_name, mode='w') as zf:
        _write_beads(beads, zf)


class _Csv:
    def __init__(self, filename, fields_str):
        header = fields_str.split(',')
        self.stream = io.StringIO()
        self.filename = filename
        self.writer = csv.DictWriter(self.stream, header)
        self.writer.writeheader()

    def add(self, row: dict):
        self.writer.writerow(row)

    def save(self, zipfile: ZipFile):
        zipfile.writestr(self.filename, self.stream.getvalue())


def _write_beads(beads, zipfile: ZipFile):
    """
    Persist Dummys (or Beads) to csv streams.
    """

    beads_csv = _Csv('beads.csv', 'box,name,kind,content_id,freeze_time,freshness')
    inputs_csv = _Csv('inputs.csv', 'owner,name,kind,content_id,freeze_time')
    input_maps_csv = _Csv('input_maps.csv', 'box,name,content_id,input,bead_name')

    for bead in beads:
        beads_csv.add(
            {
                'box': bead.box_name,
                'name': bead.name,
                'kind': bead.kind,
                'content_id': bead.content_id,
                'freeze_time': bead.timestamp_str,
                'freshness': bead.freshness.name,
            })
        for input in bead.inputs:
            inputs_csv.add(
                {
                    'owner': bead.content_id,
                    'name': input.name,
                    'kind': input.kind,
                    'content_id': input.content_id,
                    'freeze_time': input.timestamp_str
                })
        input_map = bead.input_map
        for input_nick in input_map:
            input_maps_csv.add(
                {
                    'box': bead.box_name,
                    'name': bead.name,
                    'content_id': bead.content_id,
                    'input': input_nick,
                    'bead_name': input_map.get(input_nick)
                })

    beads_csv.save(zipfile)
    inputs_csv.save(zipfile)
    input_maps_csv.save(zipfile)


def read_beads(file_name) -> List[Dummy]:
    with ZipFile(file_name) as zf:
        with zf.open('inputs.csv') as f:
            inputs_by_owner = _read_inputs(f)
        with zf.open('input_maps.csv') as f:
            input_maps_by_owner = _read_input_maps(f)
        with zf.open('beads.csv') as f:
            return _read_beads(f, inputs_by_owner, input_maps_by_owner)


def _read_csv(csv_stream):
    records = list(csv.DictReader(io.TextIOWrapper(csv_stream)))
    return records


def _read_inputs(csv_stream):
    inputs_by_owner = defaultdict(list)
    for raw_input in _read_csv(csv_stream):
        input = InputSpec(
            raw_input['name'],
            raw_input['kind'],
            raw_input['content_id'],
            raw_input['freeze_time'])
        inputs_by_owner[raw_input['owner']].append(input)
    return dict(inputs_by_owner)


def _read_input_maps(csv_stream):
    # (box, name, content_id) -> [(input-nick, bead_name)]
    input_maps_by_owner = defaultdict(dict)
    for row in _read_csv(csv_stream):
        owner = (row['box'], row['name'], row['content_id'])
        input_maps_by_owner[owner][row['input']] = row['bead_name']
    return input_maps_by_owner


def _read_beads(beads_csv_stream, inputs_by_owner, input_maps_by_owner):
    """
    Read back persisted Dummy-s.
    """
    beads = [
        Dummy(
            kind=rb['kind'],
            timestamp_str=rb['freeze_time'],
            content_id=rb['content_id'],
            inputs=inputs_by_owner.get(rb['content_id'], ()),
            input_map=input_maps_by_owner.get((rb['box'], rb['name'], rb['content_id'])),
            name=rb['name'],
            box_name=rb['box'],
            freshness=Freshness[rb['freshness']],
        )
        for rb in _read_csv(beads_csv_stream)]
    for bead in beads:
        attr.validate(bead)
    return beads
