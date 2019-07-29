import csv
from dataclasses import dataclass
import html
from typing import Hashable

from collections import defaultdict
from enum import Enum
import itertools

from bead.tech.timestamp import time_from_timestamp
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
    bead_writer = (
        csv.DictWriter(beads_csv_stream, 'box name kind content_id freeze_time'.split()))
    inputs_writer = (
        csv.DictWriter(inputs_csv_stream, 'owner name kind content_id freeze_time'.split()))
    input_maps_writer = (
        csv.DictWriter(input_maps_csv_stream, 'box name content_id input bead_name'.split()))

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


@dataclass(order=True, frozen=True)
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
    __slots__ = ('name', 'content_id')
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


def is_phantom(bead):
    return bead.state == BeadState.PHANTOM


class Cluster:
    """
    Versions of beads having the same name.
    """
    def __init__(self, name):
        self.name = name
        self.beads_by_content_id = {}

    def add(self, bead):
        assert bead.content_id not in self.beads_by_content_id
        self.beads_by_content_id[bead.content_id] = bead

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

    def get_head(self):
        """
        Latest bead, that is not phantom, or the first phantom bead, if all are phantoms.
        """
        beads = iter(self.beads())
        head = next(beads)
        return next(itertools.dropwhile(is_phantom, beads), head)

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


@dataclass
class Edge:
    src: Hashable
    dest: Hashable
    label: str

    def reversed(self):
        return Edge(self.dest, self.src, self.label)


def generate_input_edges(bead):
    """
    Generate all the 'Edge's leading from the bead to its inputs.

    An edge is a triple of (src, dest, label)
    where both 'src' and 'dest' are BeadID-s.
    """
    src = BeadID(bead.name, bead.content_id)
    for input in bead.inputs:
        dest = BeadID(bead.get_bead_name(input.name), input.content_id)
        yield Edge(src, dest, label=input.name)


def group_by_src(edges):
    """
    Make a dictionary of 'Edge's, which maps a src node to a list of 'Edge's rooted there.
    """
    edges_by_src = defaultdict(list)
    for edge in edges:
        edges_by_src[edges.src].append(edge)
    return edges_by_src


def closure(root, edges_by_src):
    """
    Return the set of reachable nodes from roots.
    edges_by_src is a dictionary of {src: [Edge]}, where `src` is a node equal to `edge.src`.
    """
    reachable = {}
    todo = set(root)
    while todo:
        src = todo.pop()
        reachable.add(src)
        for edge in edges_by_src[src]:
            if edge.dest not in reachable:
                todo.add(edge.dest)
    return reachable


def reverse(edges):
    """
    Generate reversed edges.
    """
    return (edge.reversed() for edge in edges)


class Weaver:
    """
    Visualize the web of beads with GraphViz.

    Calculation status is color coded.

    - display connections between beads and their up-to-dateness.
    """
    def __init__(self, beads):
        self.cluster_by_name = {}
        self.set_beads(beads)

    def set_beads(self, beads):
        for bead in beads:
            self._add_bead(MetaBead.from_bead(bead))

        # assign colors based on bead's up-to-date status
        self._add_phantom_beads()
        self._color_beads()

    @property
    def clusters(self):
        return self.cluster_by_name.values()

    def _add_bead(self, bead):
        try:
            cluster = self.cluster_by_name[bead.name]
        except KeyError:
            cluster = self.cluster_by_name[bead.name] = Cluster(bead.name)

        cluster.add(bead)

    def has_bead(self, name, content_id):
        return name in self.cluster_by_name and self.cluster_by_name.has(content_id)

    def generate_beads(self):
        for cluster in self.clusters:
            for bead in cluster.beads:
                yield bead

    def restrict_to(self, bead_names):
        """
        Restrict output to closure of bead content_ids on inputs from root set.
        """
        self.content_ids_to_plot = set()
        unprocessed_content_ids = set(root_content_ids)
        while unprocessed_content_ids:
            content_id = unprocessed_content_ids.pop()
            self.content_ids_to_plot.add(content_id)
            # add all not yet visited inputs to unprocessed_content_ids
            bead = self.content_id_to_bead.get(content_id)
            if bead is not None:
                unprocessed_content_ids.update(
                    input.content_id
                    for input in bead.inputs
                    if input.content_id not in self.content_ids_to_plot)

    def _add_phantom_beads(self):
        """
        Add missing input beads as PhantomBeads
        """
        for cluster in list(self.clusters):
            for bead in cluster.beads:
                for input in bead.inputs:
                    input_bead_name = bead.get_bead_name(input.name)
                    if not self.has_bead(input_bead_name, input.content_id):
                        phantom = MetaBead.phantom_from_input(input_bead_name, input)
                        self._add_bead(phantom)

    def generate_edges(self):
        """
        Generate all the edges between all the beads in the clusters
        as defined by their inputs.
        """
        for bead in self.generate_beads():
            yield from generate_input_edges(bead)

    def generate_head_edges(self):
        for cluster in self.clusters:
            head_bead = cluster.get_head()
            yield from generate_input_edges(head_bead)

    def _color_beads(self):
        """
        Assign states to beads.
        """
        cluster_heads = [cluster.get_head() for cluster in self.clusters]
        cluster_head_by_name = {bead.name: bead for bead in cluster_heads}

        # assign UP_TO_DATE for latest members of each cluster
        for head in cluster_heads:
            head.set_state(BeadState.UP_TO_DATE)

        # downgrade latest members of each cluster, if out of date
        processed = {}
        todo = set(cluster_head_by_name)

        def dfs_paint(bead):
            for input in bead.inputs:
                input_bead_name = bead.get_bead_name(input.name)
                input_bead = cluster_head_by_name[input_bead_name]
                if input_bead_name not in processed:
                    dfs_paint(input_bead)
                if ((input_bead.state != BeadState.UP_TO_DATE)
                    or (input_bead.content_id != bead.content_id)):
                        bead.set_state(BeadState.OUT_OF_DATE)
                        break
            processed.add(bead.name)
            todo.remove(bead.name)

        while todo:
            dfs_paint(next(iter(todo)))

    @property
    def beads_to_plot(self):
        for content_id in self.content_ids_to_plot:
            yield self.content_id_to_bead[content_id]

    def weave(self, do_all_edges):
        """
        Generate GraphViz .dot file describing the connections between beads
        and their up-to-dateness.
        """
        return DOT_GRAPH_TEMPLATE.format(
            bead_clusters=self.format_bead_clusters(),
            bead_inputs=self.format_inputs(do_all_edges))

    def format_bead_clusters(self):
        return '  \n'.join(cluster.as_dot for cluster in self.clusters)

    def format_inputs(self, do_all_edges):
        def edges_to_plot():
            for bead in self.beads_to_plot:
                is_auxiliary_edge = bead.state not in (BeadState.OUT_OF_DATE, BeadState.UP_TO_DATE)
                if is_auxiliary_edge and not do_all_edges:
                    continue

                for input in bead.inputs:
                    if input.content_id in self.content_ids_to_plot:
                        input_bead = self.content_id_to_bead[input.content_id]
                        yield dot_edge(input_bead, bead, input.name, is_auxiliary_edge)
        return '\n'.join(edges_to_plot())


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
    a series extra nodes and edges between them.
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
