import html
from .bead_state import BeadState


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


class Port:
    def __init__(self, bead):
        content_id = bead.content_id
        self.input = f"in_{content_id}"
        self.output = f"out_{content_id}"


def dot_edge(bead_src, bead_dest, name, is_auxiliary_edge):
    """
    Create an edge with a label in the DOT language between two beads.

    This is more complicated, than one might think,
    because GraphViz's output is unreadable for DAGs with several parallel paths:
    edges are overlapped, producing a messy graph.
    To amend this a conceptual edge is implemented with
    a series of extra nodes and edges between them.
    """
    src = f'{node_cluster(bead_src)}:{Port(bead_src).output}:e'
    dest = f'{node_cluster(bead_dest)}:{Port(bead_dest).input}:w'
    before_label = [src]
    after_label = [dest]
    silent_helper_nodes = []
    color = bead_color(bead_src) if not is_auxiliary_edge else 'grey90'
    label = html.escape(name)

    # add auxiliary nodes before label
    for _ in range(4):
        unique_node = _get_unique_node_id()
        before_label.append(unique_node)
        silent_helper_nodes.append(unique_node)

    def long_path(nodes):
        if len(nodes) > 1:
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


def dot_cluster_as_fragments(beads):
    assert beads
    # beads are sorted in descending order by timestamp
    timestamps = [b.timestamp for b in beads]
    assert timestamps == sorted(timestamps, reverse=True)
    # they have the same name
    names = {bead.name for bead in beads}
    assert names == {beads[0].name}

    label = html.escape(beads[0].name)

    yield node_cluster(beads[0])
    yield '[shape="plaintext" color="grey" '
    yield 'label=<<TABLE CELLBORDER="1">\n'
    yield '    <TR>'
    yield '<TD BORDER="0"></TD>'
    yield '<TD BORDER="0">'
    yield f'<B><I>{label}</I></B>'
    yield '</TD>'
    yield '</TR>\n'
    for bead in beads:
        color = f'BGCOLOR="{bead_color(bead)}:none" style="radial"'
        yield '    <TR>'
        yield f'<TD PORT="{Port(bead).input}" {color}></TD>'
        yield f'<TD PORT="{Port(bead).output}" {color}>'
        yield f'{bead.timestamp}'
        yield '</TD>'
        yield '</TR>\n'
    yield '</TABLE>>'
    yield ']'


# auxiliary node generator
_unique_node_counter = 0


def _get_unique_node_id():
    """
    Generate unique graphviz dot node ids.
    """
    global _unique_node_counter
    _unique_node_counter += 1
    return f"unique_{_unique_node_counter}"
