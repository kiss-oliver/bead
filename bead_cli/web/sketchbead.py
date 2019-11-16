from typing import Dict, List, Optional

import attr

from bead.meta import InputSpec
from bead.tech.timestamp import time_from_timestamp
from .bead_state import BeadState


def none_to_empty_dict(v):
    """attr converter"""
    if v is None:
        return {}
    return v


@attr.s
class SketchBead:
    """
    A bead.Bead look-alike when looking only at the metadata.

    Also has metadata for coloring (state).
    """

    content_id: str = attr.ib(kw_only=True)
    kind: str = attr.ib(kw_only=True)
    inputs: List[InputSpec] = attr.ib(kw_only=True, factory=list, converter=list)
    timestamp_str: str = attr.ib(kw_only=True)
    name: str = attr.ib(kw_only=True, default="UNKNOWN")
    input_map: Dict[str, str] = attr.ib(kw_only=True, factory=dict, converter=none_to_empty_dict)
    state: BeadState = attr.ib(kw_only=True, default=BeadState.SUPERSEDED)
    box_name: Optional[str] = attr.ib(kw_only=True, default=None)

    @property
    def timestamp(self):
        return time_from_timestamp(self.timestamp_str)

    @classmethod
    def from_bead(cls, bead):
        return cls(
            inputs=bead.inputs,
            input_map=bead.input_map,
            content_id=bead.content_id,
            kind=bead.kind,
            name=bead.name,
            timestamp_str=bead.timestamp_str,
            box_name=bead.box_name)

    @classmethod
    def phantom_from_input(cls, name: str, inputspec: InputSpec):
        """
        Create phantom beads from inputs.

        The returned bead is referenced as input from another bead,
        but we do not have the referenced bead.
        """
        phantom = (
            cls(
                name=name,
                content_id=inputspec.content_id,
                kind=inputspec.kind,
                timestamp_str=inputspec.timestamp_str))
        phantom.state = BeadState.PHANTOM
        return phantom

    def set_state(self, state):
        # phantom beads do not change state
        if self.state != BeadState.PHANTOM:
            self.state = state

    @property
    def is_not_phantom(self):
        return self.state != BeadState.PHANTOM

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

    def __repr__(self):
        cls = self.__class__.__name__
        kind = self.kind[:8]
        content_id = self.content_id[:8]
        inputs = repr(self.inputs)
        return f"{cls}:{self.name}:{kind}:{content_id}:{self.state}:{inputs}:{self.input_map}"
