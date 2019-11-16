import pytest

from tests.sketcher import Sketcher
from bead_cli.web.web import BeadWeb, BeadState


def test_new_version_marks_older_superseded():
    sketcher = Sketcher()
    sketcher.define('a1')

    web = BeadWeb.from_beads(tuple(sketcher.beads))
    web.color_beads()

    assert bead(web, 'a1').state == BeadState.UP_TO_DATE

    sketcher = Sketcher()
    sketcher.define('a1 a2')

    web = BeadWeb.from_beads(tuple(sketcher.beads))
    web.color_beads()

    assert bead(web, 'a1').state == BeadState.SUPERSEDED
    assert bead(web, 'a2').state == BeadState.UP_TO_DATE

    sketcher = Sketcher()
    sketcher.define('a1 a2 a3')

    web = BeadWeb.from_beads(tuple(sketcher.beads))
    web.color_beads()

    assert bead(web, 'a1').state == BeadState.SUPERSEDED
    assert bead(web, 'a2').state == BeadState.SUPERSEDED
    assert bead(web, 'a3').state == BeadState.UP_TO_DATE


def test_unconnected():
    sketcher = Sketcher()
    sketcher.define('a1 a2 b1 c2')

    web = BeadWeb.from_beads(tuple(sketcher.beads))
    web.color_beads()

    assert bead(web, 'a1').state == BeadState.SUPERSEDED
    assert bead(web, 'a2').state == BeadState.UP_TO_DATE
    assert bead(web, 'b1').state == BeadState.UP_TO_DATE
    assert bead(web, 'c2').state == BeadState.UP_TO_DATE


def test_up_to_date_input():
    sketcher = Sketcher()
    sketcher.define('a1 b1')
    sketcher.compile(
        """
        a1 -> b1
        """
    )

    web = BeadWeb.from_beads(tuple(sketcher.beads))
    web.color_beads()

    assert bead(web, 'a1').state == BeadState.UP_TO_DATE
    assert bead(web, 'b1').state == BeadState.UP_TO_DATE

    sketcher = Sketcher()
    sketcher.define('a1 a2 b1')
    sketcher.compile(
        """
        a2 -> b1
        """
    )

    web = BeadWeb.from_beads(tuple(sketcher.beads))
    web.color_beads()

    assert bead(web, 'a1').state == BeadState.SUPERSEDED

    assert bead(web, 'a2').state == BeadState.UP_TO_DATE
    assert bead(web, 'b1').state == BeadState.UP_TO_DATE


def test_out_of_date_input():
    sketcher = Sketcher()
    sketcher.define('a1 a2 b1')
    sketcher.compile(
        """
        a1 -> b1
        """
    )

    web = BeadWeb.from_beads(tuple(sketcher.beads))
    web.color_beads()

    assert bead(web, 'a1').state == BeadState.SUPERSEDED
    assert bead(web, 'b1').state == BeadState.OUT_OF_DATE


def test_phantom_input():
    sketcher = Sketcher()
    sketcher.define('d1 e1')
    sketcher.phantom('d1')
    sketcher.compile(
        """
        d1 --> e1
        """
    )

    web = BeadWeb.from_beads(tuple(sketcher.beads))
    web.color_beads()

    assert {'e'} == {bead.name for bead in sketcher.beads}
    assert len(list(sketcher.beads)) == 1
    assert len(web.beads) == 2

    assert bead(web, 'd1').state == BeadState.PHANTOM
    assert bead(web, 'e1').state == BeadState.OUT_OF_DATE


def test_impossible_loop():
    # sketcher are always forming a DAG, so this can not happen
    sketcher = Sketcher()
    sketcher.define('a1 b1')
    sketcher.compile(
        """
        a1 -> b1
        b1 -> a1
        """
    )

    web = BeadWeb.from_beads(tuple(sketcher.beads))
    with pytest.raises(ValueError):
        web.color_beads()


def test_coloring_is_transitive():
    sketcher = Sketcher()
    sketcher.define('a1    c1 d1 e1')
    sketcher.define('a2 b2 c2      ')
    sketcher.phantom('c1')
    sketcher.compile(
        """
        a1          c1 -> d1 -> e1
        a2 -> b2 -> c2
        """
    )

    web = BeadWeb.from_beads(tuple(sketcher.beads))
    web.color_beads()

    assert bead(web, 'a1').state == BeadState.SUPERSEDED
    assert bead(web, 'c1').state == BeadState.PHANTOM
    assert bead(web, 'd1').state == BeadState.OUT_OF_DATE
    assert bead(web, 'e1').state == BeadState.OUT_OF_DATE

    assert bead(web, 'a2').state == BeadState.UP_TO_DATE
    assert bead(web, 'b2').state == BeadState.UP_TO_DATE
    assert bead(web, 'c2').state == BeadState.UP_TO_DATE


def bead(web, bead_id):
    for bead in web.beads:
        if bead.content_id == f'content_id_{bead_id}':
            return bead
    raise ValueError('SketchBead by bead id not found', bead_id)
