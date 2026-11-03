"""Kern gegen Handrechnung (Mini-Instanzen aus conftest.py) und eine Gegenprobe ohne Code aus dem Algorithmus-Modul (DEMO-PLAYBOOK §1b und §12)."""

import itertools

import pytest

import mtr_algorithm as A
import mtr_constants as C
from mtr_scenario import Instance, make_instance, with_costs


def _own_forest(inst, ids):
    """Eigene Kreisprüfung für die Gegenprobe: Komponenten-Etiketten statt Union-Find und Tiefensuche."""
    label = list(range(inst.n))
    for e in ids:
        u, v, _ = inst.edges[e]
        if label[u] == label[v]:
            return False
        old, new = label[v], label[u]
        label = [new if x == old else x for x in label]
    return True


def test_kruskal_by_hand_on_the_mini_instance(mini):
    steps = A.greedy_steps(mini)
    assert [s.edge for s in steps] == [1, 2, 6, 0, 3, 4, 5]                      # nach (Kosten, Index): 1, 2, 3, 4, 5, 8, 10
    assert [s.status for s in steps] == ["genommen", "genommen", "genommen", "Kreis", "genommen", "Kreis", "Kreis"]
    assert A.taken(steps) == (1, 2, 6, 3) and A.cost_of(mini, A.taken(steps)) == 11


def test_the_mini_instance_has_21_spanning_trees_and_the_cheapest_two_cost_11_and_13(mini):
    trees = A.all_trees(mini)
    assert len(trees) == 21
    assert sorted(A.cost_of(mini, t) for t in trees)[:2] == [11, 13]
    best, opts = A.optimum_trees(mini)
    assert best == 11 and opts == [(1, 2, 3, 6)]


def test_swap_by_hand_14_to_11(mini):
    tree = (1, 2, 4, 6)                                                           # A-C, B-C, C-D, D-E: 1 + 2 + 8 + 3 = 14
    assert A.cost_of(mini, tree) == 14
    assert sorted(A.cycle_edges(mini, tree, 3)) == [2, 4]                        # B-D schließt den Kreis B-C-D
    assert A.improving_swaps(mini, tree) == [(3, 4)]                             # nur C-D (8) ist teurer als B-D (5) und liegt auf dem Kreis
    after = A.apply_swap(tree, 3, 4)
    assert after == (1, 2, 3, 6) and A.cost_of(mini, after) == 11


def test_second_swap_by_hand_13_to_11(mini):
    tree = (0, 1, 3, 6)                                                           # A-B, A-C, B-D, D-E: 4 + 1 + 5 + 3 = 13
    assert A.improving_swaps(mini, tree) == [(2, 0)]                             # B-C hinein (2), A-B heraus (4)
    assert A.cost_of(mini, A.apply_swap(tree, 2, 0)) == 11


def test_the_optimal_tree_has_no_improving_swap(mini):
    assert A.improving_swaps(mini, (1, 2, 3, 6)) == []


def test_swap_search_from_every_one_of_the_21_trees_ends_at_cost_11(mini):
    for tree in A.all_trees(mini):
        for rule in ("zufällig", "bester"):
            swaps = A.local_search(mini, tree, 0, rule, seed=3)
            end = A.apply_swaps(tree, swaps)
            assert A.check_tree(mini, end) and A.cost_of(mini, end) == 11, (tree, rule)
            assert A.improving_swaps(mini, end) == []


def test_every_swap_strictly_lowers_the_cost(mini):
    for tree in A.all_trees(mini):
        cost = A.cost_of(mini, tree)
        for e, f in A.local_search(mini, tree, 0, "zufällig", seed=1):
            tree = A.apply_swap(tree, e, f)
            assert A.cost_of(mini, tree) < cost
            cost = A.cost_of(mini, tree)


def test_degree_bound_blocks_a_greedy_edge_and_leaves_no_tree(engpass):
    steps = A.greedy_steps(engpass, 2)
    assert [(s.edge, s.status) for s in steps] == [(0, "genommen"), (1, "genommen"), (2, "Grad"), (3, "Kreis"), (4, "genommen")]
    assert len(A.taken(steps)) == 3 < engpass.n - 1                               # kein Spannbaum
    best, opts = A.optimum_trees(engpass, 2)
    assert best == 10 and sorted(opts) == [(0, 2, 3, 4), (1, 2, 3, 4)]
    assert len(A.all_trees(engpass)) == 3                                         # ohne Schranke gibt es drei


def test_greedy_with_degree_bound_can_be_worse_than_the_optimum(bruecke):
    taken = A.taken(A.greedy_steps(bruecke, 2))
    assert taken == (0, 1, 4) and A.cost_of(bruecke, taken) == 7
    best, opts = A.optimum_trees(bruecke, 2)
    assert best == 6 and sorted(opts) == [(0, 2, 3), (1, 2, 3)]
    assert A.taken(A.greedy_steps(bruecke)) == (0, 1, 2) and A.cost_of(bruecke, (0, 1, 2)) == 4   # ohne Schranke Kosten 4


def test_swap_is_blocked_by_the_degree_bound(engpass):
    tree = (0, 2, 3, 4)                                                           # A-B, A-D, B-C, D-E, Kosten 10
    assert A.improving_swaps(engpass, tree, 0) == [(1, 3)]                       # ohne Schranke: A-C hinein, B-C heraus (Kosten 8)
    assert A.improving_swaps(engpass, tree, 2) == []                             # mit Schranke würde A drei Leitungen haben
    assert A.swap_ok(engpass, tree, 1, 3, 0) and not A.swap_ok(engpass, tree, 1, 3, 2)


def test_swap_ok_rejects_wrong_arguments(mini):
    tree = (1, 2, 4, 6)
    assert not A.swap_ok(mini, tree, 1, 4)    # Kante schon im Baum
    assert not A.swap_ok(mini, tree, 3, 6)    # D-E liegt nicht auf dem Kreis von B-D
    assert A.swap_ok(mini, tree, 3, 4)


def test_forest_and_tree_checker(mini):
    assert A.check_forest(mini, ()) and A.check_forest(mini, (1, 2, 6))
    assert not A.check_forest(mini, (0, 1, 2))            # Kreis A-B-C
    assert not A.check_forest(mini, (1, 1))               # doppelt
    assert not A.check_forest(mini, (7,)) and not A.check_forest(mini, (-1,))
    assert A.check_tree(mini, (1, 2, 3, 6)) and not A.check_tree(mini, (1, 2, 6))
    assert not A.check_forest(mini, (1, 2, 4), 2)          # C hätte drei Leitungen (A-C, B-C, C-D)
    assert A.check_forest(mini, (1, 2, 4), 3)


def test_forest_enumeration_matches_an_independent_count(mini):
    own = [c for r in range(mini.m + 1) for c in itertools.combinations(range(mini.m), r) if _own_forest(mini, c)]
    assert sorted(A.enumerate_forests(mini)) == sorted(own)
    own2 = [c for c in own if max(A.degrees(mini, c), default=0) <= 2]
    assert sorted(A.enumerate_forests(mini, 2)) == sorted(own2)


def test_best_forest_costs_by_hand(mini):
    best = A.best_forest_costs(mini)
    assert best == {0: 0, 1: 1, 2: 3, 3: 6, 4: 11}                                # 1; 1 + 2; 1 + 2 + 3; 1 + 2 + 3 + 5


def test_prefix_costs_are_the_running_sums_of_the_taken_edges(mini):
    assert A.prefix_costs(mini, A.greedy_steps(mini)) == [1, 3, 6, 11]


def test_greedy_is_optimal_on_40_random_plans_without_bound():
    for seed in range(40):
        inst = make_instance(6 + seed % 4, seed, hub=bool(seed % 2))
        taken = A.taken(A.greedy_steps(inst))
        best, _ = A.optimum_trees(inst)
        assert A.check_tree(inst, taken) and A.cost_of(inst, taken) == best, seed


def test_shortest_path_tree_by_hand(mini):
    tree = A.shortest_path_tree(mini)
    assert {1, 2, 3} <= tree and len(tree) == 4                                   # C über A-C, B über B-C, D über B-D; E ist ein Gleichstand (11 über D oder C)
    assert len(tree & {5, 6}) == 1


def test_transformations_are_strictly_increasing():
    values = [float(c) for c in range(1, 301)]
    for name in C.TRANSFORMS:
        out = [A.transform(name, c) for c in values]
        assert all(b > a for a, b in zip(out, out[1:])), name


def test_unknown_transformation_raises(mini):
    with pytest.raises(ValueError):
        A.transform("unbekannt", 3.0)


def test_with_costs_keeps_the_graph_and_rejects_wrong_length(mini):
    other = with_costs(mini, [1, 2, 3, 4, 5, 6, 7])
    assert other.points == mini.points and [(u, v) for u, v, _ in other.edges] == [(u, v) for u, v, _ in mini.edges]
    with pytest.raises(ValueError):
        with_costs(mini, [1, 2])


def test_make_instance_is_deterministic_connected_and_has_the_documented_edge_count():
    for n in range(2, 10):
        a, b = make_instance(n, 5), make_instance(n, 5)
        assert a == b and a.m == min(n * (n - 1) // 2, 2 * n - 2)
        assert A.components(a, range(a.m)) == 1
        assert all(u < v and c >= 1 for u, v, c in a.edges)


def test_hub_only_lowers_the_cost_of_edges_at_the_depot():
    plain, hub = make_instance(8, 3), make_instance(8, 3, hub=True)
    assert [(u, v) for u, v, _ in plain.edges] == [(u, v) for u, v, _ in hub.edges]
    for (u, v, c1), (_, _, c2) in zip(plain.edges, hub.edges):
        assert c2 == c1 if u != 0 else c2 < c1 or c1 == 1
    assert any(u == 0 for u, _, _ in plain.edges)
