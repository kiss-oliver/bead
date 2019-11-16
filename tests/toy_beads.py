import datetime
import string
from typing import Dict, Optional

from bead.meta import InputSpec
from bead_cli.web.sketchbead import SketchBead
from bead_cli.web.graph import BeadID


TS_BASE = datetime.datetime(
    year=2000, month=1, day=1, tzinfo=datetime.timezone.utc
)


class ToyBeads:
    """
    Factory of fake, but properly connected SketchBead-s.

    For use in test fixtures and to create coherent bead web graphs for docs.
    a1 is older than a2, a9 is older than b1
    """
    def __init__(self):
        self._by_name: Dict[str, SketchBead] = {}
        self._phantoms = set()

    def __getitem__(self, name):
        return self._by_name[name]

    def define(self, protos: str, kind: str = '*', box_name: str = 'main'):
        # 'a1 a2 b3 c4'
        for proto in protos.split():
            bead = self._create(proto, proto, kind, box_name, inputs=[])
            self._by_name[proto] = bead

    def clone(self, proto: str, name: str, box_name: str):
        assert name not in self._by_name
        proto_bead = self._by_name[proto]
        bead = self._create(proto, name, proto_bead.kind, box_name, proto_bead.inputs)
        self._by_name[name] = bead

    def map_input(self, bead_name: str, input_name: str, input_bead_name: str):
        bead = self._by_name[bead_name]
        self._map_input(bead, input_name, input_bead_name)

    def compile(self, dag: str):
        # 'a1 -a-> b2 -> c4 a2 -another-a-> b2'
        label = None
        src: Optional[SketchBead] = None
        for fragment in dag.split():
            if fragment.startswith("-"):
                label = fragment.rstrip(">").strip("-").strip(":")
            else:
                dest = self._by_name[fragment]
                if src is not None and label is not None:
                    self._add_input(dest, label or src.name, src)
                    label = None
                src = dest

    def phantom(self, name_versions: str):
        self._phantoms.update(set(name_versions.split()))

    def id_for(self, *names):
        for name in names:
            yield BeadID.from_bead(self._by_name[name])

    def _create(self, proto, name, kind, box_name, inputs):
        # proto ~ [a-z][0-9]
        proto_name, proto_version = proto
        assert proto_name.islower()
        assert proto_version.isdigit()
        delta_from_name = (
            datetime.timedelta(
                days=string.ascii_lowercase.index(proto_name)))
        delta_from_version = datetime.timedelta(hours=int(proto_version))
        timestamp = TS_BASE + delta_from_name + delta_from_version
        bead = SketchBead(
            name=name.rstrip(string.digits),
            kind=kind,
            content_id=f"content_id_{proto}",
            timestamp_str=timestamp.strftime('%Y%m%dT%H%M%S%f%z'),
            box_name=box_name,
        )
        # ensure, that we are using the given inputs
        # it is important for clones to keep being clones, even if new input is added
        bead.inputs = inputs
        return bead

    def _add_input(self, bead, input_name, input_bead):
        assert input_name not in [i.name for i in bead.inputs]
        input_spec = InputSpec(
            name=input_name,
            kind=input_bead.kind,
            content_id=input_bead.content_id,
            timestamp_str=input_bead.timestamp_str,
        )
        bead.inputs.append(input_spec)
        self._map_input(bead, input_name, input_bead.name)

    def _map_input(self, bead, input_name, input_bead_name):
        assert input_name in [i.name for i in bead.inputs]
        bead.set_input_bead_name(input_name, input_bead_name)

    def __iter__(self):
        for name, bead in self._by_name.items():
            if name not in self._phantoms:
                yield bead


if __name__ == '__main__':
    beads = ToyBeads()
    beads.define('a1 a2', kind='kind1', box_name='secret')
    beads.define('b2', kind='kind2')
    beads.define('c4', kind='kind3')
    beads.define('z9', kind='KK')
    # beads.phantom('a1 a2')
    beads.compile(
        """
        a1 -:older:-> b2 -> c4
        a2 -:newer:-> b2
        """
    )
    beads.clone('b2', 'clone123', 'clone-box')
    beads.map_input('clone123', 'newer', 'axon')
    beads.map_input('clone123', 'older', 'neuron')

    from pprint import pprint
    pprint(list(beads))
    pprint([o.__dict__ for o in beads])
