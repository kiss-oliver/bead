from collections import defaultdict
from typing import Iterable, Dict, List, Set, Iterator, TypeVar

import attr

from .dummy import Dummy


Bead = TypeVar('Bead')


@attr.s(frozen=True, slots=True, auto_attribs=True)
class Ref:
    """
    Unique reference for loaded beads.

    NOTE: Using multiple boxes can make this reference non-unique, as it is possible to
    have beads with same name and content, but with different input-maps.
    This could happen e.g. for sets of beads that are "branched" - released - and
    possibly need separate future maintenance.

    This potential non-unique-ness can be mitigated by having `update` search for updates
    in the same box, the workspace was developed from.
    """
    name: str
    content_id: str

    @classmethod
    def from_bead(cls, bead) -> 'Ref':
        return cls(bead.name, bead.content_id)

    @classmethod
    def index_for(cls, beads: Iterable[Bead]) -> Dict['Ref', Bead]:
        bead_by_ref = {}
        for bead in beads:
            bead_by_ref[cls.from_bead(bead)] = bead
        return bead_by_ref


@attr.s(auto_attribs=True)
class Edge:
    src: Dummy
    dest: Dummy
    label: str

    def reversed(self):
        return Edge(self.dest, self.src, self.label)


def generate_input_edges(bead_index: Dict[Ref, Dummy], bead) -> Iterator[Edge]:
    """
    Generate all the 'Edge's leading from the bead to its inputs.

    Modifies bead_index - adds referenced, but missing beads as phantom beads.

    An edge is a triple of (src, dest, label), where both 'src' and 'dest' are Dummy-s.
    """
    for input in bead.inputs:
        src_bead_name = bead.get_input_bead_name(input.name)
        src_ref = Ref(src_bead_name, input.content_id)
        try:
            src = bead_index[src_ref]
        except LookupError:
            src = bead_index[src_ref] = Dummy.phantom_from_input(src_bead_name, input)

        yield Edge(src, bead, input.name)


def group_by_src(edges) -> Dict[Ref, List[Edge]]:
    """
    Make a dictionary of 'Edge's, which maps a src node to a list of 'Edge's rooted there.
    """
    edges_by_src: Dict[Ref, List[Edge]] = defaultdict(list)
    for edge in edges:
        edges_by_src[Ref.from_bead(edge.src)].append(edge)
    return edges_by_src


def group_by_dest(edges) -> Dict[Ref, List[Edge]]:
    """
    Make a dictionary of 'Edge's, which maps a node to a list of 'Edge's going there.
    """
    edges_by_dest: Dict[Ref, List[Edge]] = defaultdict(list)
    for edge in edges:
        edges_by_dest[Ref.from_bead(edge.dest)].append(edge)
    return edges_by_dest


def closure(roots: List[Ref], edges_by_src: Dict[Ref, List[Edge]]):
    """
    Return the set of reachable nodes from roots.
    edges_by_src is edges grouped by their `src`.
    """
    reachable: Set[Ref] = set()
    todo: Set[Ref] = set(roots)
    while todo:
        src = todo.pop()
        reachable.add(src)
        for edge in edges_by_src[src]:
            dest_id = Ref.from_bead(edge.dest)
            if dest_id not in reachable:
                todo.add(dest_id)
    return reachable


def reverse(edges: Iterable[Edge]) -> Iterator[Edge]:
    """
    Generate reversed edges.
    """
    return (edge.reversed() for edge in edges)
