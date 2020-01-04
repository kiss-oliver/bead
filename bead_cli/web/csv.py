import csv
from collections import defaultdict
from contextlib import ExitStack
import io
from typing import Callable, Dict, List

import attr

from bead.meta import InputSpec
from .dummy import Dummy, Freshness


def write_beads(file_base, beads: List[Dummy]):
    with BeadMetaCsvStreams.for_writing(file_base) as streams:
        streams.write_beads(beads)


def read_beads(file_base) -> List[Dummy]:
    with BeadMetaCsvStreams.for_reading(file_base) as streams:
        return streams.read_beads()


@attr.s
class BeadMetaCsvStreams:
    beads: io.TextIOBase = attr.ib()
    inputs: io.TextIOBase = attr.ib()
    input_maps: io.TextIOBase = attr.ib()
    close: Callable[[], None] = attr.ib(default=(lambda: None))

    @classmethod
    def for_reading(cls, base):
        return cls.open_all(base, mode='r')

    @classmethod
    def for_writing(cls, base):
        return cls.open_all(base, mode='w')

    @classmethod
    def open_all(cls, base, mode):
        field_to_file_name = cls.get_file_names_by_fields(base)
        assert 'close' not in field_to_file_name
        assert set(field_to_file_name) - set(attr.fields_dict(cls)) == set()
        exit_stack = ExitStack()
        attrs = {}
        for field, file_name in field_to_file_name.items():
            try:
                attrs[field] = exit_stack.enter_context(open(file_name, mode))
            except:
                exit_stack.close()
                raise
        return cls(**attrs, close=exit_stack.pop_all().close)

    @classmethod
    def get_file_names_by_fields(cls, base) -> Dict[str, str]:
        return {
            'beads': f'{base}_beads.csv',
            'inputs': f'{base}_inputs.csv',
            'input_maps': f'{base}_input_maps.csv',
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def read_beads(self):
        return _read_beads(self.beads, self.inputs, self.input_maps)

    def write_beads(self, beads):
        _write_beads(beads, self.beads, self.inputs, self.input_maps)


def _read_csv(csv_stream):
    records = list(csv.DictReader(csv_stream))
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


def _read_beads(beads_csv_stream, inputs_csv_stream, input_maps_csv_stream):
    """
    Read back persisted Dummy-s.
    """
    inputs_by_owner = _read_inputs(inputs_csv_stream)
    input_maps_by_owner = _read_input_maps(input_maps_csv_stream)
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


def _write_beads(beads, beads_csv_stream, inputs_csv_stream, input_maps_csv_stream):
    """
    Persist Dummys (or Beads) to csv streams.
    """
    def header(csv_header):
        return csv_header.split(',')
    bead_writer = (
        csv.DictWriter(beads_csv_stream, header('box,name,kind,content_id,freeze_time,freshness')))
    inputs_writer = (
        csv.DictWriter(inputs_csv_stream, header('owner,name,kind,content_id,freeze_time')))
    input_maps_writer = (
        csv.DictWriter(input_maps_csv_stream, header('box,name,content_id,input,bead_name')))

    bead_writer.writeheader()
    inputs_writer.writeheader()
    input_maps_writer.writeheader()
    for bead in beads:
        bead_writer.writerow(
            {
                'box': bead.box_name,
                'name': bead.name,
                'kind': bead.kind,
                'content_id': bead.content_id,
                'freeze_time': bead.timestamp_str,
                'freshness': bead.freshness.name,
            })
        for input in bead.inputs:
            inputs_writer.writerow(
                {
                    'owner': bead.content_id,
                    'name': input.name,
                    'kind': input.kind,
                    'content_id': input.content_id,
                    'freeze_time': input.timestamp_str
                })
        input_map = bead.input_map
        for input_nick in input_map:
            input_maps_writer.writerow(
                {
                    'box': bead.box_name,
                    'name': bead.name,
                    'content_id': bead.content_id,
                    'input': input_nick,
                    'bead_name': input_map.get(input_nick)
                })
