from bead_cli.web.web import BeadWeb
from bead_cli.web.graph import BeadID, group_by_src, closure, reverse

from tests.toy_beads import ToyBeads


def test_one_path():
    toy_beads = ToyBeads()
    toy_beads.define('a1 b1 c1 d1 e1')
    toy_beads.compile('a1 -> b1 -> c1 -> d1 -> e1')
    web = BeadWeb.from_beads(tuple(toy_beads))
    edges_by_src = group_by_src(web.edges)

    reachable = closure([BeadID.from_bead(toy_beads['c1'])], edges_by_src)

    assert reachable == set(toy_beads.id_for('c1', 'd1', 'e1'))


def test_two_paths():
    toy_beads = ToyBeads()
    toy_beads.define('a1 b1 c1 d1 e1')
    toy_beads.define('a2 b2 c2 d2 e2')
    toy_beads.compile('a1 -> b1 -> c1 -> d1 -> e1')
    toy_beads.compile('a2 -> b2 -> c2 -> d2 -> e2')
    web = BeadWeb.from_beads(tuple(toy_beads))
    edges_by_src = group_by_src(web.edges)

    reachable = closure(list(toy_beads.id_for('c1', 'c2')), edges_by_src)

    assert reachable == set(toy_beads.id_for('c1', 'd1', 'e1', 'c2', 'd2', 'e2'))


def test_forked_path():
    toy_beads = ToyBeads()
    toy_beads.define('a1 b1 c1 d1 e1')
    toy_beads.define('a2 b2 c2 d2 e2')
    toy_beads.compile('a1 -> b1 -> c1 --> d1 -> e1')
    toy_beads.compile('            c1 -:fork:-> d2')
    toy_beads.compile('a2 -> b2 -> c2 --> d2 -> e2')
    web = BeadWeb.from_beads(tuple(toy_beads))
    edges_by_src = group_by_src(web.edges)

    reachable = closure(list(toy_beads.id_for('c1')), edges_by_src)

    assert reachable == set(toy_beads.id_for('c1', 'd1', 'e1', 'd2', 'e2'))


def test_loop():
    # it is an impossible bead config,
    # but in general loops should not cause problems to closure calculation
    toy_beads = ToyBeads()
    toy_beads.define('a1 b1 c1')
    toy_beads.compile('a1 -> b1 -> c1 -> a1')
    web = BeadWeb.from_beads(tuple(toy_beads))
    edges_by_src = group_by_src(web.edges)

    reachable = closure(list(toy_beads.id_for('b1')), edges_by_src)

    assert reachable == set(toy_beads.id_for('a1', 'b1', 'c1'))


def test_reverse():
    toy_beads = ToyBeads()
    toy_beads.define('a1 b1 c1 d1 e1')
    toy_beads.compile('a1 -> b1 -> c1 -> d1 -> e1')
    web = BeadWeb.from_beads(tuple(toy_beads))
    edges_by_src = group_by_src(reverse(web.edges))

    reachable = closure([BeadID.from_bead(toy_beads['c1'])], edges_by_src)

    assert reachable == set(toy_beads.id_for('a1', 'b1', 'c1'))
