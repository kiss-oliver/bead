import pytest

from tests.toy_beads import ToyBeads
from bead_cli.web.web import BeadWeb, BeadState


def test_new_version_marks_older_superseded():
    beads = ToyBeads()
    beads.define('a1')

    web = BeadWeb.from_beads(tuple(beads))
    web.color_beads()

    assert bead(web, 'a1').state == BeadState.UP_TO_DATE

    beads = ToyBeads()
    beads.define('a1 a2')

    web = BeadWeb.from_beads(tuple(beads))
    web.color_beads()

    assert bead(web, 'a1').state == BeadState.SUPERSEDED
    assert bead(web, 'a2').state == BeadState.UP_TO_DATE

    beads = ToyBeads()
    beads.define('a1 a2 a3')

    web = BeadWeb.from_beads(tuple(beads))
    web.color_beads()

    assert bead(web, 'a1').state == BeadState.SUPERSEDED
    assert bead(web, 'a2').state == BeadState.SUPERSEDED
    assert bead(web, 'a3').state == BeadState.UP_TO_DATE


def test_unconnected():
    beads = ToyBeads()
    beads.define('a1 a2 b1 c2')

    web = BeadWeb.from_beads(tuple(beads))
    web.color_beads()

    assert bead(web, 'a1').state == BeadState.SUPERSEDED
    assert bead(web, 'a2').state == BeadState.UP_TO_DATE
    assert bead(web, 'b1').state == BeadState.UP_TO_DATE
    assert bead(web, 'c2').state == BeadState.UP_TO_DATE


def test_up_to_date_input():
    beads = ToyBeads()
    beads.define('a1 b1')
    beads.compile(
        """
        a1 -> b1
        """
    )

    web = BeadWeb.from_beads(tuple(beads))
    web.color_beads()

    assert bead(web, 'a1').state == BeadState.UP_TO_DATE
    assert bead(web, 'b1').state == BeadState.UP_TO_DATE

    beads = ToyBeads()
    beads.define('a1 a2 b1')
    beads.compile(
        """
        a2 -> b1
        """
    )

    web = BeadWeb.from_beads(tuple(beads))
    web.color_beads()

    assert bead(web, 'a1').state == BeadState.SUPERSEDED

    assert bead(web, 'a2').state == BeadState.UP_TO_DATE
    assert bead(web, 'b1').state == BeadState.UP_TO_DATE


def test_out_of_date_input():
    beads = ToyBeads()
    beads.define('a1 a2 b1')
    beads.compile(
        """
        a1 -> b1
        """
    )

    web = BeadWeb.from_beads(tuple(beads))
    web.color_beads()

    assert bead(web, 'a1').state == BeadState.SUPERSEDED
    assert bead(web, 'b1').state == BeadState.OUT_OF_DATE


def test_phantom_input():
    beads = ToyBeads()
    beads.define('d1 e1')
    beads.phantom('d1')
    beads.compile(
        """
        d1 --> e1
        """
    )

    web = BeadWeb.from_beads(tuple(beads))
    web.color_beads()

    assert {'e'} == {bead.name for bead in beads}
    assert len(list(beads)) == 1
    assert len(web.beads) == 2

    assert bead(web, 'd1').state == BeadState.PHANTOM
    assert bead(web, 'e1').state == BeadState.OUT_OF_DATE


def test_impossible_loop():
    # beads are always forming a DAG, so this can not happen
    beads = ToyBeads()
    beads.define('a1 b1')
    beads.compile(
        """
        a1 -> b1
        b1 -> a1
        """
    )

    web = BeadWeb.from_beads(tuple(beads))
    with pytest.raises(ValueError):
        web.color_beads()


def test_coloring_is_transitive():
    beads = ToyBeads()
    beads.define('a1    c1 d1 e1')
    beads.define('a2 b2 c2      ')
    beads.phantom('c1')
    beads.compile(
        """
        a1          c1 -> d1 -> e1
        a2 -> b2 -> c2
        """
    )

    web = BeadWeb.from_beads(tuple(beads))
    web.color_beads()

    assert bead(web, 'a1').state == BeadState.SUPERSEDED
    assert bead(web, 'c1').state == BeadState.PHANTOM
    assert bead(web, 'd1').state == BeadState.OUT_OF_DATE
    assert bead(web, 'e1').state == BeadState.OUT_OF_DATE

    assert bead(web, 'a2').state == BeadState.UP_TO_DATE
    assert bead(web, 'b2').state == BeadState.UP_TO_DATE
    assert bead(web, 'c2').state == BeadState.UP_TO_DATE


def bead(web, toy_id):
    for bead in web.beads:
        if bead.content_id == f'content_id_{toy_id}':
            return bead
    raise ValueError('Bead by toy id not found', toy_id)
