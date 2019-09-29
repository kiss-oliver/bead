from collections import defaultdict
from typing import Iterable, Dict, List, Set, Iterator, TypeVar

import attr

from bead.meta import InputSpec
from .metabead import MetaBead


Bead = TypeVar('Bead')


@attr.s(frozen=True, slots=True, auto_attribs=True)
class BeadID:
    """
    Unique identifier for loaded beads.

    NOTE: Using multiple boxes can make this identifier non-unique, as it is possible to
    have beads with same name and content, but with different input-maps.
    This could happen e.g. for sets of beads that are "branched" - released - and
    possibly need separate future maintenance.

    This potential non-unique-ness can be mitigated by having `update` search for updates
    in the same box, the workspace was developed from.
    """
    name: str
    content_id: str

    @classmethod
    def from_bead(cls, bead) -> 'BeadID':
        return BeadID(bead.name, bead.content_id)

    @classmethod
    def index_for(cls, beads: Iterable[Bead]) -> Dict['BeadID', Bead]:
        bead_by_id = {}
        for bead in beads:
            bead_by_id[cls.from_bead(bead)] = bead
        return bead_by_id


NodeRef = BeadID


@attr.s(auto_attribs=True)
class Edge:
    src: NodeRef
    dest: NodeRef
    input: InputSpec

    @property
    def label(self):
        return input.name

    def reversed(self):
        return Edge(self.dest, self.src, self.input)

    def create_phantom_source(self):
        return MetaBead.phantom_from_input(self.src.name, self.input)


def generate_input_edges(bead) -> Iterator[Edge]:
    """
    Generate all the 'Edge's leading from the bead to its inputs.

    An edge is a triple of (src, dest, label), where both 'src' and 'dest' are BeadID-s.
    """
    dest = BeadID(bead.name, bead.content_id)
    for input in bead.inputs:
        src = BeadID(bead.get_input_bead_name(input.name), input.content_id)
        yield Edge(src, dest, input)


def group_by_src(edges) -> Dict[NodeRef, List[Edge]]:
    """
    Make a dictionary of 'Edge's, which maps a src node to a list of 'Edge's rooted there.
    """
    edges_by_src: Dict[NodeRef, List[Edge]] = defaultdict(list)
    for edge in edges:
        edges_by_src[edges.src].append(edge)
    return edges_by_src


def group_by_dest(edges) -> Dict[NodeRef, List[Edge]]:
    """
    Make a dictionary of 'Edge's, which maps a node to a list of 'Edge's going there.
    """
    edges_by_dest: Dict[NodeRef, List[Edge]] = defaultdict(list)
    for edge in edges:
        edges_by_dest[edges.dest].append(edge)
    return edges_by_dest


def closure(roots: List[NodeRef], edges_by_src: Dict[NodeRef, List[Edge]]):
    """
    Return the set of reachable nodes from roots.
    edges_by_src is edges grouped by their `src`.
    """
    reachable = set()
    todo: Set[NodeRef] = set(roots)
    while todo:
        src = todo.pop()
        reachable.add(src)
        for edge in edges_by_src[src]:
            if edge.dest not in reachable:
                todo.add(edge.dest)
    return reachable


def reverse(edges: Iterable[Edge]):
    """
    Generate reversed edges.
    """
    return (edge.reversed() for edge in edges)
