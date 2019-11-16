from bead_cli.web.web import BeadWeb
from bead_cli.web.graph import BeadID, group_by_src, closure, reverse

from tests.sketcher import Sketcher


def test_one_path():
    sketcher = Sketcher()
    sketcher.define('a1 b1 c1 d1 e1')
    sketcher.compile('a1 -> b1 -> c1 -> d1 -> e1')
    web = BeadWeb.from_beads(tuple(sketcher.beads))
    edges_by_src = group_by_src(web.edges)

    reachable = closure([BeadID.from_bead(sketcher['c1'])], edges_by_src)

    assert reachable == set(sketcher.id_for('c1', 'd1', 'e1'))


def test_two_paths():
    sketcher = Sketcher()
    sketcher.define('a1 b1 c1 d1 e1')
    sketcher.define('a2 b2 c2 d2 e2')
    sketcher.compile('a1 -> b1 -> c1 -> d1 -> e1')
    sketcher.compile('a2 -> b2 -> c2 -> d2 -> e2')
    web = BeadWeb.from_beads(tuple(sketcher.beads))
    edges_by_src = group_by_src(web.edges)

    reachable = closure(list(sketcher.id_for('c1', 'c2')), edges_by_src)

    assert reachable == set(sketcher.id_for('c1', 'd1', 'e1', 'c2', 'd2', 'e2'))


def test_forked_path():
    sketcher = Sketcher()
    sketcher.define('a1 b1 c1 d1 e1')
    sketcher.define('a2 b2 c2 d2 e2')
    sketcher.compile('a1 -> b1 -> c1 --> d1 -> e1')
    sketcher.compile('            c1 -:fork:-> d2')
    sketcher.compile('a2 -> b2 -> c2 --> d2 -> e2')
    web = BeadWeb.from_beads(tuple(sketcher.beads))
    edges_by_src = group_by_src(web.edges)

    reachable = closure(list(sketcher.id_for('c1')), edges_by_src)

    assert reachable == set(sketcher.id_for('c1', 'd1', 'e1', 'd2', 'e2'))


def test_loop():
    # it is an impossible bead config,
    # but in general loops should not cause problems to closure calculation
    sketcher = Sketcher()
    sketcher.define('a1 b1 c1')
    sketcher.compile('a1 -> b1 -> c1 -> a1')
    web = BeadWeb.from_beads(tuple(sketcher.beads))
    edges_by_src = group_by_src(web.edges)

    reachable = closure(list(sketcher.id_for('b1')), edges_by_src)

    assert reachable == set(sketcher.id_for('a1', 'b1', 'c1'))


def test_reverse():
    sketcher = Sketcher()
    sketcher.define('a1 b1 c1 d1 e1')
    sketcher.compile('a1 -> b1 -> c1 -> d1 -> e1')
    web = BeadWeb.from_beads(tuple(sketcher.beads))
    edges_by_src = group_by_src(reverse(web.edges))

    reachable = closure([BeadID.from_bead(sketcher['c1'])], edges_by_src)

    assert reachable == set(sketcher.id_for('a1', 'b1', 'c1'))
