import html

from bead.tech.timestamp import EPOCH_STR

from .metabead import MetaBead
from .bead_state import BeadState
from . import graphviz


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
            return (bead.is_not_phantom, bead.timestamp)

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
            yield graphviz.node_cluster(beads[0])
            yield '[shape="plaintext" color="grey" '
            yield 'label=<<TABLE CELLBORDER="1">\n'
            yield '    <TR>'
            yield '<TD BORDER="0"></TD>'
            yield '<TD BORDER="0">'
            yield f'<B><I>{html.escape(beads[0].name)}</I></B>'
            yield '</TD>'
            yield '</TR>\n'
            for bead in beads:
                color = f'BGCOLOR="{graphviz.bead_color(bead)}:none" style="radial"'
                yield '    <TR>'
                yield f'<TD PORT="{graphviz.port(bead, "in")}" {color}></TD>'
                yield f'<TD PORT="{graphviz.port(bead, "out")}" {color}>'
                yield f'{bead.timestamp}'
                yield '</TD>'
                yield '</TR>\n'
            yield '</TABLE>>'
            yield ']'
        return ''.join(fragments())
