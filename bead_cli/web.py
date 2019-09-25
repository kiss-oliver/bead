import csv
import attr
import itertools
import html
from typing import Iterable, Dict, List, Set, Iterator, TypeVar, Generic

from collections import defaultdict
from enum import Enum

from bead.tech.timestamp import time_from_timestamp, EPOCH_STR
from bead.meta import InputSpec


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


class BeadState(Enum):
    PHANTOM = 0,
    # (red) unknown bead
    SUPERSEDED = 1,
    # (grey) not latest in cluster
    UP_TO_DATE = 2,
    # (green) latest and all its inputs are also referencing an UP_TO_DATE
    OUT_OF_DATE = 3,
    # (yellow) latest in cluster, but needs updating, because of newer input version


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


def bead_id(bead):
    return BeadID(bead.name, bead.content_id)


class MetaBead:
    """
    A bead.Bead look-alike when looking only at the metadata.

    Also has metadata for coloring (state).
    """
    def __init__(self, kind, timestamp_str, content_id,
                 inputs=(),
                 input_map=None,
                 box_name=None,
                 name="UNKNOWN"):
        self.inputs = inputs
        self.input_map = input_map if input_map else {}
        self.content_id = content_id
        self.box_name = box_name
        self.name = name
        self.kind = kind
        self.timestamp_str = timestamp_str
        self.timestamp = time_from_timestamp(timestamp_str)
        self.state = BeadState.SUPERSEDED

    @classmethod
    def from_bead(cls, bead):
        return cls(
            inputs=tuple(bead.inputs),
            input_map=bead.input_map,
            content_id=bead.content_id,
            kind=bead.kind,
            name=bead.name,
            timestamp_str=bead.timestamp_str,
            box_name=bead.box_name)

    @classmethod
    def phantom_from_input(cls, name, inputspec):
        """
        Create phantom beads from inputs.

        The returned bead is referenced as input from another bead,
        but we do not have the referenced bead.
        """
        phantom = cls(
            name=name,
            content_id=inputspec.content_id,
            kind=inputspec.kind,
            timestamp_str=inputspec.timestamp_str)
        phantom.state = BeadState.PHANTOM
        return phantom

    def set_state(self, state):
        # phantom beads do not change state
        if self.state != BeadState.PHANTOM:
            self.state = state

    def __repr__(self):
        cls = self.__class__.__name__
        kind = self.kind[:8]
        content_id = self.content_id[:8]
        inputs = repr(self.inputs)
        return f"{cls}:{self.name}:{kind}:{content_id}:{self.state}:{inputs}"

    def get_bead_name(self, input_nick):
        '''
        Returns the bead name on which update works.
        '''
        return self.input_map.get(input_nick, input_nick)

    def set_bead_name(self, input_nick, bead_name):
        '''
        Sets the bead name to be used for updates in the future.
        '''
        self.input_map[input_nick] = bead_name


def is_not_phantom(bead):
    return bead.state != BeadState.PHANTOM


class Cluster:
    """
    Versions of beads having the same name.

    .head: Latest bead, that is not phantom, or the first phantom bead, if all are phantoms.
    """
    def __init__(self, name):
        self.name = name
        self.beads_by_content_id = {}

        # use a phantom bead instead of None for default value
        phantom_head = MetaBead(
            name=name, timestamp_str=EPOCH_STR,
            content_id=None, kind='EMPTY CLUSTER')
        phantom_head.set_state(BeadState.PHANTOM)
        self.head = phantom_head

    def add(self, bead):
        assert bead.content_id not in self.beads_by_content_id
        self.beads_by_content_id[bead.content_id] = bead

        def head_order(bead):
            return (is_not_phantom(bead), bead.timestamp)

        if head_order(bead) >= head_order(self.head):
            self.head = bead

    def beads(self):
        """
        Time sorted list of beads, most recent first.
        """
        return (
            sorted(
                self.beads_by_content_id.values(),
                key=(lambda bead: bead.timestamp),
                reverse=True))

    def has(self, content_id):
        return content_id in self.beads_by_content_id

    def get(self, content_id):
        return self.beads_by_content_id[content_id]

    @property
    def as_dot(self):
        # beads are sorted in descending order by timestamp
        beads = self.beads()
        assert beads
        names = {bead.name for bead in beads}
        assert len(names) == 1
        assert names == {self.name}

        def fragments():
            yield node_cluster(beads[0])
            yield '[shape="plaintext" color="grey" '
            yield 'label=<<TABLE CELLBORDER="1">\n'
            yield '    <TR>'
            yield '<TD BORDER="0"></TD>'
            yield '<TD BORDER="0">'
            yield f'<B><I>{html.escape(beads[0].name)}</I></B>'
            yield '</TD>'
            yield '</TR>\n'
            for bead in beads:
                color = f'BGCOLOR="{bead_color(bead)}:none" style="radial"'
                yield '    <TR>'
                yield f'<TD PORT="{port(bead, "in")}" {color}></TD>'
                yield f'<TD PORT="{port(bead, "out")}" {color}>'
                yield f'{bead.timestamp}'
                yield '</TD>'
                yield '</TR>\n'
            yield '</TABLE>>'
            yield ']'
        return ''.join(fragments())


NodeRef = TypeVar('NodeRef', BeadID, str)


@attr.s(auto_attribs=True)
class Edge(Generic[NodeRef]):
    src: NodeRef
    dest: NodeRef
    label: str  # FIXME: make label an InputSpec (could make phantoms from edges!)

    def reversed(self):
        return Edge(self.dest, self.src, self.label)


def generate_input_edges(bead) -> Iterator[Edge[BeadID]]:
    """
    Generate all the 'Edge's leading from the bead to its inputs.

    An edge is a triple of (src, dest, label), where both 'src' and 'dest' are BeadID-s.
    """
    dest = BeadID(bead.name, bead.content_id)
    for input in bead.inputs:
        src = BeadID(bead.get_bead_name(input.name), input.content_id)
        yield Edge(src, dest, label=input.name)


def group_by_src(edges) -> Dict[NodeRef, List[Edge]]:
    """
    Make a dictionary of 'Edge's, which maps a src node to a list of 'Edge's rooted there.
    """
    edges_by_src: Dict[NodeRef, List[Edge[NodeRef]]] = defaultdict(list)
    for edge in edges:
        edges_by_src[edges.src].append(edge)
    return edges_by_src


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


def _has_bead(cluster_by_name, name, content_id):
    return name in cluster_by_name and cluster_by_name[name].has(content_id)


def _add_bead(cluster_by_name, bead):
    try:
        cluster = cluster_by_name[bead.name]
    except KeyError:
        cluster = cluster_by_name[bead.name] = Cluster(bead.name)

    cluster.add(bead)


def _add_phantom_beads(cluster_by_name, beads):
    """
    Add missing input beads as PhantomBeads
    """
    for bead in beads:
        for input in bead.inputs:
            input_bead_name = bead.get_bead_name(input.name)
            if not _has_bead(cluster_by_name, input_bead_name, input.content_id):
                phantom = MetaBead.phantom_from_input(input_bead_name, input)
                _add_bead(cluster_by_name, phantom)


class BeadWeb:
    """
    A consistent graph of beads and input links between them.
    """

    def __init__(self, clusters: List[Cluster], edges: List[Edge]):
        self.clusters = clusters
        self.cluster_by_name = {c.name: c for c in clusters}

        # all edges are expected to refer to links between existing beads in the clusters
        def has(bead_id):
            return _has_bead(self.cluster_by_name, bead_id.name, bead_id.content_id)

        bad_edges = [e for e in edges if not has(e.src) or not has(e.dest)]
        assert bad_edges == [], bad_edges
        self.edges = edges

    def get_bead(self, bead_id: BeadID) -> MetaBead:
        cluster = self.cluster_by_name[bead_id.name]
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

                    yield dot_edge(input_bead, bead, label, is_auxiliary_edge)
            return '\n'.join(edges_as_dot())

        return DOT_GRAPH_TEMPLATE.format(
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
                input_bead_name = bead.get_bead_name(input.name)
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
        cluster_by_name: Dict[str, Cluster] = {}
        metabeads = []
        for bead in beads:
            bead = MetaBead.from_bead(bead)
            metabeads.append(bead)
            _add_bead(cluster_by_name, bead)

        _add_phantom_beads(cluster_by_name, metabeads)
        edges = itertools.chain.from_iterable(generate_input_edges(bead) for bead in metabeads)
        return cls(list(cluster_by_name.values()), list(edges))

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


DOT_GRAPH_TEMPLATE = """\
digraph {{
  layout=dot
  rankdir="LR"
  pad="1"
  pack="true"
  packmode="node"

  // clustered node definitions
{bead_clusters}

  // edges: input links
  edge [headport="w" tailport="e"]
  // edge [weight="100"]
  // edge [labelfloat="true"]
  edge [decorate="true"]
{bead_inputs}
}}
"""


def node_cluster(bead):
    id = bead.name.replace('"', '\\"')
    return f'"cluster_{id}"'


BEAD_COLOR = {
    BeadState.PHANTOM: "red",
    BeadState.SUPERSEDED: "grey",
    BeadState.UP_TO_DATE: "green",
    BeadState.OUT_OF_DATE: "orange",
}


def bead_color(bead):
    return BEAD_COLOR[bead.state]


def port(bead, port_type):
    assert port_type in ("in", "out")
    return f"{port_type}_{bead.content_id}"


_unique_node_counter = 0


def _get_unique_node_id():
    """
    Generate unique node ids.
    """
    global _unique_node_counter
    _unique_node_counter += 1
    return f"uniq_{_unique_node_counter}"


def dot_edge(bead_src, bead_dest, name, is_auxiliary_edge):
    """
    Create an edge with a label in the DOT language between two beads.

    This is more complicated, than one might think,
    because GraphViz's output is unreadable for DAGs with several parallel paths:
    edges are overlapped, producing a messy graph.
    To amend this a conceptual edge is implemented with
    a series of extra nodes and edges between them.
    """
    src = f'{node_cluster(bead_src)}:{port(bead_src, "out")}:e'
    dest = f'{node_cluster(bead_dest)}:{port(bead_dest, "in")}:w'
    before_label = [src]
    after_label = [dest]
    silent_helper_nodes = []
    color = bead_color(bead_src) if not is_auxiliary_edge else 'grey90'
    label = html.escape(name)

    def add_before_label():
        unique_node = _get_unique_node_id()
        before_label.append(unique_node)
        silent_helper_nodes.append(unique_node)

    def add_after_label():
        unique_node = _get_unique_node_id()
        after_label.insert(0, unique_node)
        silent_helper_nodes.append(unique_node)

    for _ in range(4):
        add_before_label()

    def long_path(nodes):
        if len(nodes) > 1:
            # return ' -> '.join(nodes) + f'[color={color} headport="w" tailport="e"];'
            return ' -> '.join(nodes) + f'[color={color}];'
        return ''

    return ''.join(
        [f' {node}[shape=plain label=""];' for node in silent_helper_nodes]
        + [long_path(before_label)]
        + [
            f'  {before_label[-1]} -> {after_label[0]} ',
            f'[fontcolor="{color}" color="{color}" fontsize="10" label="{label}" weight="100"]',
            ';'
        ]
        + [long_path(after_label)])
