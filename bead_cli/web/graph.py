from collections import defaultdict
from typing import Iterable, Dict, List, Set, Iterator

import attr
from cached_property import cached_property

from .dummy import Dummy, Ref


Node = Dummy


@attr.s(auto_attribs=True, frozen=True)
class Edge:
    src: Node
    dest: Node
    label: str

    def reversed(self):
        return Edge(self.dest, self.src, self.label)

    @cached_property
    def src_ref(self):
        return self.src.ref

    @cached_property
    def dest_ref(self):
        return self.dest.ref


def generate_input_edges(bead_index: Dict[Ref, Dummy], bead) -> Iterator[Edge]:
    """
    Generate all the 'Edge's leading from the bead to its inputs.

    Modifies bead_index - adds referenced, but missing beads as phantom beads.

    An edge is a triple of (src, dest, label), where both 'src' and 'dest' are Dummy-s.
    """
    for input in bead.inputs:
        src_ref = Ref.from_bead_input(bead, input)
        try:
            src = bead_index[src_ref]
        except LookupError:
            src = bead_index[src_ref] = Dummy.phantom_from_input(bead, input)

        yield Edge(src, bead, input.name)


def group_by_src(edges) -> Dict[Ref, List[Edge]]:
    """
    Make a dictionary of 'Edge's, which maps a src node to a list of 'Edge's rooted there.
    """
    edges_by_src: Dict[Ref, List[Edge]] = defaultdict(list)
    for edge in edges:
        edges_by_src[edge.src_ref].append(edge)
    return edges_by_src


def group_by_dest(edges) -> Dict[Ref, List[Edge]]:
    """
    Make a dictionary of 'Edge's, which maps a node to a list of 'Edge's going there.
    """
    edges_by_dest: Dict[Ref, List[Edge]] = defaultdict(list)
    for edge in edges:
        edges_by_dest[edge.dest_ref].append(edge)
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
            dest_id = edge.dest_ref
            if dest_id not in reachable:
                todo.add(dest_id)
    return reachable


def reverse(edges: Iterable[Edge]) -> Iterator[Edge]:
    """
    Generate reversed edges.
    """
    return (edge.reversed() for edge in edges)
