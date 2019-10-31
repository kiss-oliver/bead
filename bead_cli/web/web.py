import itertools

from typing import Dict, List, Tuple, Set

import attr

from .bead_state import BeadState
from .metabead import MetaBead
from .cluster import Cluster, create_cluster_index
from . import graphviz
from .graph import Edge, BeadID, generate_input_edges, group_by_dest


@attr.s(frozen=True, slots=True, auto_attribs=True)
class BeadWeb:
    beads: Tuple[MetaBead, ...]
    edges: Tuple[Edge, ...]

    @classmethod
    def from_beads(cls, metabeads: Tuple[MetaBead, ...]):
        bead_index = BeadID.index_for(metabeads)
        edges = tuple(
            itertools.chain.from_iterable(
                generate_input_edges(bead_index, bead)
                for bead in metabeads))
        return cls(tuple(bead_index.values()), edges)

    def create_cluster_index(self) -> Dict[str, Cluster]:
        return create_cluster_index(self.beads)

    def create_bead_index(self) -> Dict[BeadID, MetaBead]:
        return BeadID.index_for(self.beads)

    def color_beads(self):
        color_beads(self)

    def as_dot(self):
        return plot_clusters_as_dot(self)


def simplify(web: BeadWeb) -> BeadWeb:
    """
    Remove unreferenced clusters and beads.

    Makes a new instance
    """
    raise NotImplementedError


def heads(web: BeadWeb) -> BeadWeb:
    """
    Keep only cluster heads and their inputs.

    Makes a new instance
    """
    raise NotImplementedError


def set_sources(web: BeadWeb, cluster_names: List[str]) -> BeadWeb:
    """
    Drop all clusters, that are not reachable from the named clusters.

    Makes a new instance
    """
    raise NotImplementedError


def set_sinks(web: BeadWeb, cluster_names: List[str]) -> BeadWeb:
    """
    Drop all clusters, that do not lead to any of the named clusters.

    Makes a new instance
    """
    raise NotImplementedError


def drop_before(web: BeadWeb, timestamp) -> BeadWeb:
    """
    Keep only beads, that are after the given timestamp.

    Makes a new instance
    """
    raise NotImplementedError


def drop_after(web: BeadWeb, timestamp) -> BeadWeb:
    """
    Keep only beads, that are before the timestamp.

    Makes a new instance
    """
    raise NotImplementedError


def plot_clusters_as_dot(web: BeadWeb):
    """
    Generate GraphViz .dot file content, which describe the connections between beads
    and their up-to-date status.
    """
    clusters = web.create_cluster_index().values()
    formatted_bead_clusters = '  \n'.join(c.as_dot for c in clusters)

    def format_inputs():
        def edges_as_dot():
            for edge in web.edges:
                is_auxiliary_edge = (
                    edge.dest.state not in (BeadState.OUT_OF_DATE, BeadState.UP_TO_DATE))

                yield graphviz.dot_edge(edge.src, edge.dest, edge.label, is_auxiliary_edge)
        return '\n'.join(edges_as_dot())

    return graphviz.DOT_GRAPH_TEMPLATE.format(
        bead_clusters=formatted_bead_clusters,
        bead_inputs=format_inputs())


def color_beads(web: BeadWeb):
    """
    Assign up-to-date states to beads.
    """
    cluster_by_name = web.create_cluster_index()
    edges_by_dest = group_by_dest(web.edges)

    # reset colors
    for bead in web.beads:
        bead.set_state(BeadState.SUPERSEDED)

    # assign UP_TO_DATE for latest members of each cluster
    # (phantom states are not overwritten)
    for cluster in cluster_by_name.values():
        cluster.head.set_state(BeadState.UP_TO_DATE)

    # downgrade latest members of each cluster, if out of date
    processed: Set[str] = set()
    todo = set(cluster_by_name)
    path: Set[str] = set()

    def dfs_paint(bead):
        if bead.name in path:
            raise ValueError('Loop detected between connections!', bead)
        path.add(bead.name)
        for input_edge in edges_by_dest[BeadID.from_bead(bead)]:
            input_bead_name = input_edge.src.name
            if input_bead_name not in cluster_by_name:
                # XXX: when an input edge has been eliminated, it will have no effect on the
                # coloring - this is controversial, as that input might be out of date/missing,
                # so it can result in different coloring, than looking at the full picture
                continue
            input_bead = cluster_by_name[input_bead_name].head
            if input_bead_name not in processed:
                dfs_paint(input_bead)
            if ((input_bead.state != BeadState.UP_TO_DATE)
                    or (input_bead.content_id != input_edge.src.content_id)):
                bead.set_state(BeadState.OUT_OF_DATE)
                break
        processed.add(bead.name)
        todo.remove(bead.name)
        path.remove(bead.name)

    while todo:
        bead = cluster_by_name[next(iter(todo))].head
        dfs_paint(bead)
