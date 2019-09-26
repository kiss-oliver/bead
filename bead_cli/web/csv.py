import csv
from collections import defaultdict

from bead.meta import InputSpec
from .metabead import MetaBead


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


def read_beads(beads_csv_stream, inputs_csv_stream, input_maps_csv_stream):
    """
    Read back persisted MetaBead-s.
    """
    inputs_by_owner = _read_inputs(inputs_csv_stream)
    input_maps_by_owner = _read_input_maps(input_maps_csv_stream)
    beads = [
        MetaBead(
            kind=rb['kind'],
            timestamp_str=rb['freeze_time'],
            content_id=rb['content_id'],
            inputs=inputs_by_owner.get(rb['content_id'], ()),
            input_map=input_maps_by_owner.get((rb['box'], rb['name'], rb['content_id'])),
            name=rb['name'],
            box_name=rb['box'])
        for rb in _read_csv(beads_csv_stream)]
    return beads


def write_beads(beads, beads_csv_stream, inputs_csv_stream, input_maps_csv_stream):
    """
    Persist MetaBeads (or Beads) to csv streams.
    """
    def header(csv_header):
        return csv_header.split(',')
    bead_writer = (
        csv.DictWriter(beads_csv_stream, header('box,name,kind,content_id,freeze_time')))
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
                'freeze_time': bead.timestamp_str
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
