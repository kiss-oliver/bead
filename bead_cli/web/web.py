import itertools

from typing import Dict, List

from .bead_state import BeadState
from .metabead import MetaBead
from .cluster import Cluster
from . import graphviz
from .graph import Edge, BeadID, generate_input_edges


class BeadWeb:
    """
    A consistent graph of beads and input links between them.
    """

    def __init__(self, clusters: List[Cluster], edges: List[Edge]):
        self.clusters = Clusters(clusters)

        # all edges are expected to refer to links between existing beads in the clusters
        def has(bead_id):
            return self.cluster_by_name.has_bead(bead_id.name, bead_id.content_id)

        bad_edges = [e for e in edges if not has(e.src) or not has(e.dest)]
        assert bad_edges == [], bad_edges
        self.edges = edges

    def get_bead(self, bead_id: BeadID) -> MetaBead:
        cluster = self.clusters[bead_id.name]
        return cluster.get(bead_id.content_id)

    def as_dot(self):
        """
        Generate GraphViz .dot file content, which describe the connections between beads
        and their up-to-date status.
        """
        formatted_bead_clusters = '  \n'.join(c.as_dot for c in self.clusters)

        def format_inputs():
            def edges_as_dot():
                for edge in self.edges:
                    bead = self.get_bead(edge.dest)
                    input_bead = self.get_bead(edge.src)
                    label = edge.label
                    is_auxiliary_edge = (
                        bead.state not in (BeadState.OUT_OF_DATE, BeadState.UP_TO_DATE))

                    yield graphviz.dot_edge(input_bead, bead, label, is_auxiliary_edge)
            return '\n'.join(edges_as_dot())

        return graphviz.DOT_GRAPH_TEMPLATE.format(
            bead_clusters=formatted_bead_clusters,
            bead_inputs=format_inputs())

    def beads(self):
        return itertools.chain.from_iterable(cluster.beads() for cluster in self.clusters)

    def reset_colors(self):
        for bead in self.beads():
            bead.set_state(BeadState.SUPERSEDED)

    def color_beads(self):
        """
        Assign states to beads.
        """
        self.reset_colors()

        cluster_heads = [cluster.head for cluster in self.clusters]
        cluster_head_by_name = {bead.name: bead for bead in cluster_heads}

        # assign UP_TO_DATE for latest members of each cluster
        for head in cluster_heads:
            head.set_state(BeadState.UP_TO_DATE)

        # downgrade latest members of each cluster, if out of date
        processed = set()
        todo = set(cluster_head_by_name)

        def dfs_paint(bead):
            for input in bead.inputs:
                input_bead_name = bead.get_input_bead_name(input.name)
                if input_bead_name not in cluster_head_by_name:
                    # XXX: when an input edge has been eliminated, it will have no effect on the
                    # coloring - this is controversial, as that input might be out of date/missing,
                    # so it can result in different coloring, than looking at the full picture
                    continue
                input_bead = cluster_head_by_name[input_bead_name]
                if input_bead_name not in processed:
                    dfs_paint(input_bead)
                if ((input_bead.state != BeadState.UP_TO_DATE)
                        or (input_bead.content_id != input.content_id)):
                    bead.set_state(BeadState.OUT_OF_DATE)
                    break
            processed.add(bead.name)
            todo.remove(bead.name)

        while todo:
            bead = cluster_head_by_name[next(iter(todo))]
            dfs_paint(bead)

    # constructors
    @classmethod
    def from_beads(cls, beads) -> 'BeadWeb':
        """
        Create a BeadWeb from the given beads, using their inputs as edge definitions.

        Also creates phantom beads to make all edges valid.
        """
        clusters = Clusters([])
        metabeads = []
        for bead in beads:
            bead = MetaBead.from_bead(bead)
            metabeads.append(bead)
            clusters.add_bead(bead)

        clusters.add_phantom_beads(metabeads)
        edges = itertools.chain.from_iterable(generate_input_edges(bead) for bead in metabeads)
        return cls(list(clusters), list(edges))

    def simplify(self) -> 'BeadWeb':
        """
        Remove unreferenced clusters and beads.

        Makes a new instance
        """
        raise NotImplementedError

    def heads(self) -> 'BeadWeb':
        """
        Keep only cluster heads and their inputs.

        Makes a new instance
        """
        raise NotImplementedError

    def set_sources(self, cluster_names: List[str]) -> 'BeadWeb':
        """
        Drop all clusters, that are not reachable from the named clusters.

        Makes a new instance
        """
        raise NotImplementedError

    def set_sinks(self, cluster_names: List[str]) -> 'BeadWeb':
        """
        Drop all clusters, that do not lead to any of the named clusters.

        Makes a new instance
        """
        raise NotImplementedError

    def drop_before(self, timestamp) -> 'BeadWeb':
        """
        Keep only beads, that are after the given timestamp.

        Makes a new instance
        """
        raise NotImplementedError

    def drop_after(self, timestamp) -> 'BeadWeb':
        """
        Keep only beads, that are before the timestamp.

        Makes a new instance
        """
        raise NotImplementedError


class Clusters:
    def __init__(self, clusters: List[Cluster]):
        self.cluster_by_name: Dict[str, Cluster] = {c.name: c for c in clusters}

    def has_bead(self, name, content_id):
        return name in self.cluster_by_name and self.cluster_by_name[name].has(content_id)

    def add_bead(self, bead):
        try:
            cluster = self.cluster_by_name[bead.name]
        except KeyError:
            cluster = self.cluster_by_name[bead.name] = Cluster(bead.name)

        cluster.add(bead)

    def add_phantom_beads(self, beads):
        """
        Add missing input beads as PhantomBeads
        """
        for bead in beads:
            for input in bead.inputs:
                input_bead_name = bead.get_input_bead_name(input.name)
                if not self.has_bead(input_bead_name, input.content_id):
                    phantom = MetaBead.phantom_from_input(input_bead_name, input)
                    self.add_bead(phantom)

    def __getitem__(self, name):
        return self.cluster_by_name[name]

    def __iter__(self):
        return iter(self.cluster_by_name.values())
