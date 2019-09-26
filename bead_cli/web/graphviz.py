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
