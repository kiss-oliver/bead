from bead.tech.timestamp import time_from_timestamp
from .bead_state import BeadState


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

    def get_input_bead_name(self, input_nick):
        '''
        Returns the bead name on which update works.
        '''
        return self.input_map.get(input_nick, input_nick)

    def set_input_bead_name(self, input_nick, bead_name):
        '''
        Sets the bead name to be used for updates in the future.
        '''
        self.input_map[input_nick] = bead_name

    @property
    def is_not_phantom(self):
        return self.state != BeadState.PHANTOM
