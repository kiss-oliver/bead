import datetime
import string
from typing import Dict

from bead.meta import InputSpec
from .metabead import MetaBead


class Beads:
    def __init__(self):
        self._by_name: Dict[str, MetaBead] = {}
        self._phantoms = set()

    def define(self, protos: str, kind='*', box_name='main'):
        # 'a1 a2 b3 c4'
        for proto in protos.split():
            name = proto[0]
            bead = self._proto_clone(proto, name, kind, box_name, inputs=[])
            self._by_name[proto] = bead

    def clone(self, proto, name, box_name):
        assert name not in self._by_name
        proto_bead = self._by_name[proto]
        bead = self._proto_clone(proto, name, proto_bead.kind, box_name, proto_bead.inputs)
        self._by_name[name] = bead

    def map_input(self, bead_name, input_name, input_bead_name):
        bead = self._by_name[bead_name]
        self._map_input(bead, input_name, input_bead_name)

    def compile(self, dag: str):
        # 'a1 -a-> b2 -> c4 a2 -another-a-> b2'
        label = None
        src: MetaBead = None
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

    def _proto_clone(self, proto, name, kind, box_name, inputs):
        # proto ~ [a-z][0-9]
        proto_name, proto_version = proto
        assert proto_name.islower()
        assert proto_version.isdigit()
        bead = MetaBead(
            name=name,
            kind=kind,
            content_id=f"id_{proto}",
            timestamp_str=datetime.datetime(
                year=2000,
                month=string.ascii_lowercase.index(proto_name) + 1,
                day=int(proto_version),
                tzinfo=datetime.timezone.utc,
            ).strftime('%Y%m%dT%H%M%S%f%z'),
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
        bead.input_map[input_name] = input_bead_name

    def __iter__(self):
        for name, bead in self._by_name.items():
            if name not in self._phantoms:
                yield bead


beads = Beads()
beads.define('a1 a2', kind='kind1', box_name='secret')
beads.define('b2', kind='kind2')
beads.define('c4', kind='kind3')
# beads.phantom('a1 a2')
beads.compile(
    """
    a1 -:older:-> b2 -> c4
    a2 -:newer:-> b2
    """
)
beads.clone('b2', 'clone', 'clone-box')
beads.map_input('clone', 'newer', 'axon')

from pprint import pprint
pprint(list(beads))
pprint([o.__dict__ for o in beads])
