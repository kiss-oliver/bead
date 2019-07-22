import csv
import html

from collections import defaultdict
from enum import Enum

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
    inputs_by_owner = _read_inputs(inputs_csv_stream)
    input_maps_by_owner = _read_input_maps(input_maps_csv_stream)
    beads = [
        Bead(
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


class Bead:
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
    def from_input(cls, name, inputspec):
        """
        Create phantom beads from inputs.

        The returned bead is referenced as input from another bead,
        but we do not have access to it.
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


def toposort(content_id_to_bead):
    """
    Topological sort for beads.

    Ordering is defined by input relations.
    """
    unseen = 0
    on_path = 1
    done = 2
    ordering_state = {content_id: unseen for content_id in content_id_to_bead}
    content_id_order = []
    todo = set(content_id_to_bead)
    path = []  # (content_id, next input index)
    while todo:
        content_id = todo.pop()
        path.append((content_id, 0))
        ordering_state[content_id] = on_path
        while path:
            content_id, next_input_index = path.pop()
            if next_input_index < len(content_id_to_bead[content_id].inputs):
                # there is an input still, that comes before current bead
                ordering_state[content_id] = on_path
                path.append((content_id, next_input_index + 1))
                content_id = content_id_to_bead[content_id].inputs[next_input_index].content_id
                if ordering_state[content_id] is unseen:
                    path.append((content_id, 0))
                    todo.remove(content_id)
                    ordering_state[content_id] = on_path
                else:
                    assert ordering_state[content_id] is done, (
                        f"bead with content_id {content_id} references itself")
            else:
                # all inputs [=dependencies] are processed, bead comes next
                ordering_state[content_id] = done
                content_id_order.append(content_id)
    assert len(content_id_order) == len(content_id_to_bead)
    return content_id_order


def cluster_beads(beads):
    """
    Sort beads into ordered lists by their :name.

    The lists are ordered descending by bead.timestamp (first one most recent)
    """
    bead_clusters = defaultdict(list)
    for bead in beads:
        bead_clusters[bead.name].append(bead)
    bead_clusters = dict(bead_clusters)

    def time_sorted_cluster(cluster_id):
        return sorted(
            bead_clusters[cluster_id],
            key=(lambda bead: bead.timestamp),
            reverse=True)
    for cluster_id in bead_clusters.keys():
        bead_clusters[cluster_id] = time_sorted_cluster(cluster_id)
    return bead_clusters


class Weaver:
    """
    Visualize the web of beads with GraphViz.

    Calculation status is color coded.

    - display connections between beads and their up-to-dateness.
    """
    def __init__(self, beads):
        self.all_beads = list(beads)
        # NOTE: this needs further work.
        # E.g. if same bead is present under different names,
        # content_id_to_bead would not be enough
        self.content_id_to_bead = {
            bead.content_id: Bead.from_bead(bead)
            for bead in self.all_beads}

        # assign colors based on bead's up-to-date status
        self.add_phantom_beads()
        # # sort beads by calculation order
        self.all_beads = [
            self.content_id_to_bead[content_id]
            for content_id in toposort(self.content_id_to_bead)]
        self.color_beads()
        # default to all-bead visualization
        self.content_ids_to_plot = set(self.content_id_to_bead)

    def restrict_to(self, root_content_ids):
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

    def add_phantom_beads(self):
        """
        Add missing input beads as PhantomBeads
        """
        for bead in self.all_beads.copy():
            for input in bead.inputs:
                # FIXME: verify presence by mapped input name and content_id
                if input.content_id not in self.content_id_to_bead:
                    # FIXME: use mapped input name as phantom.name
                    phantom = Bead.from_input(input.name, input)
                    self.content_id_to_bead[phantom.content_id] = phantom
                    self.all_beads.append(phantom)

    def color_beads(self):
        """
        Assign states to beads.
        """
        # time ordered (desc!) clusters
        bead_clusters = cluster_beads(self.all_beads)
        # assign UP_TO_DATE for latest members of each cluster
        for cluster_id in bead_clusters:
            cluster_head = bead_clusters[cluster_id][0]
            cluster_head.set_state(BeadState.UP_TO_DATE)

        # downgrade latest members of each cluster, if out of date
        for bead in self.all_beads:
            if bead.state == BeadState.UP_TO_DATE:
                out_of_date = any(
                    self.content_id_to_bead[input.content_id].state != BeadState.UP_TO_DATE
                    for input in bead.inputs)
                if out_of_date:
                    bead.set_state(BeadState.OUT_OF_DATE)

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
        bead_clusters = cluster_beads(self.beads_to_plot)
        return (
            '  \n'.join(
                self.format_cluster(
                    bead_clusters[cluster_id]) for cluster_id in bead_clusters))

    def format_cluster(self, beads):
        # beads are sorted in descending order by timestamp
        assert beads
        names = {bead.name for bead in beads}
        assert len(names) == 1

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


def get_unique_node_id():
    """
    Generate unique node ids.
    """
    global _unique_node_counter
    _unique_node_counter += 1
    return f"uniq_{_unique_node_counter}"


def dot_edge(bead_src, bead_dest, name, is_auxiliary_edge):
    src = f'{node_cluster(bead_src)}:{port(bead_src, "out")}:e'
    dest = f'{node_cluster(bead_dest)}:{port(bead_dest, "in")}:w'
    before_label = [src]
    after_label = [dest]
    silent_helper_nodes = []
    color = bead_color(bead_src) if not is_auxiliary_edge else 'grey90'
    label = html.escape(name)

    def add_before_label():
        unique_node = get_unique_node_id()
        before_label.append(unique_node)
        silent_helper_nodes.append(unique_node)

    def add_after_label():
        unique_node = get_unique_node_id()
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
