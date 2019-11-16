from collections import defaultdict
from typing import Iterable, Dict, List, Set, Iterator, TypeVar

import attr

from .sketchbead import SketchBead


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
        return cls(bead.name, bead.content_id)

    @classmethod
    def index_for(cls, beads: Iterable[Bead]) -> Dict['BeadID', Bead]:
        bead_by_id = {}
        for bead in beads:
            bead_by_id[cls.from_bead(bead)] = bead
        return bead_by_id


@attr.s(auto_attribs=True)
class Edge:
    src: SketchBead
    dest: SketchBead
    label: str

    def reversed(self):
        return Edge(self.dest, self.src, self.label)


def generate_input_edges(bead_index: Dict[BeadID, SketchBead], bead) -> Iterator[Edge]:
    """
    Generate all the 'Edge's leading from the bead to its inputs.

    Modifies bead_index - adds referenced, but missing beads as phantom beads.

    An edge is a triple of (src, dest, label), where both 'src' and 'dest' are SketchBead-s.
    """
    for input in bead.inputs:
        src_bead_name = bead.get_input_bead_name(input.name)
        src_bead_id = BeadID(src_bead_name, input.content_id)
        try:
            src = bead_index[src_bead_id]
        except LookupError:
            src = bead_index[src_bead_id] = SketchBead.phantom_from_input(src_bead_name, input)

        yield Edge(src, bead, input.name)


def group_by_src(edges) -> Dict[BeadID, List[Edge]]:
    """
    Make a dictionary of 'Edge's, which maps a src node to a list of 'Edge's rooted there.
    """
    edges_by_src: Dict[BeadID, List[Edge]] = defaultdict(list)
    for edge in edges:
        edges_by_src[BeadID.from_bead(edge.src)].append(edge)
    return edges_by_src


def group_by_dest(edges) -> Dict[BeadID, List[Edge]]:
    """
    Make a dictionary of 'Edge's, which maps a node to a list of 'Edge's going there.
    """
    edges_by_dest: Dict[BeadID, List[Edge]] = defaultdict(list)
    for edge in edges:
        edges_by_dest[BeadID.from_bead(edge.dest)].append(edge)
    return edges_by_dest


def closure(roots: List[BeadID], edges_by_src: Dict[BeadID, List[Edge]]):
    """
    Return the set of reachable nodes from roots.
    edges_by_src is edges grouped by their `src`.
    """
    reachable: Set[BeadID] = set()
    todo: Set[BeadID] = set(roots)
    while todo:
        src = todo.pop()
        reachable.add(src)
        for edge in edges_by_src[src]:
            dest_id = BeadID.from_bead(edge.dest)
            if dest_id not in reachable:
                todo.add(dest_id)
    return reachable


def reverse(edges: Iterable[Edge]) -> Iterator[Edge]:
    """
    Generate reversed edges.
    """
    return (edge.reversed() for edge in edges)
