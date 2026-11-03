"""Orakel-Tests: Kernroutinen gegen einen anderen Rechenweg (DEMO-PLAYBOOK §12, ORACLE-PLAYBOOK).

Orakel: (1) Zahl der Spannbäume über den Matrix-Baum-Satz (Determinante in exakten Brüchen), (2) Spannbäume und Optimum durch Aufzählen aller
Kantenmengen mit eigener Kreisprüfung (Komponenten-Etiketten), (3) networkx für den billigsten Spannbaum und die Wegekosten des Baums der
billigsten Wege, (4) Aufzählen aller Teilmengen für die besten Wälder je Größe, (5) Zulässigkeit jedes Ergebnisses mit dem Prüfer des Moduls und
zusätzlich unabhängig. Alles unter 10 s."""

import itertools
from fractions import Fraction

import pytest

import mtr_algorithm as A
from mtr_scenario import make_instance


def _acyclic(inst, ids):
    label = list(range(inst.n))
    for e in ids:
        u, v, _ = inst.edges[e]
        if label[u] == label[v]:
            return False
        old, new = label[v], label[u]
        label = [new if x == old else x for x in label]
    return True


def _degree_ok(inst, ids, maxdeg):
    count = [0] * inst.n
    for e in ids:
        count[inst.edges[e][0]] += 1
        count[inst.edges[e][1]] += 1
    return not maxdeg or max(count, default=0) <= maxdeg


def _trees_by_combinations(inst, maxdeg=0):
    return [c for c in itertools.combinations(range(inst.m), inst.n - 1) if _acyclic(inst, c) and _degree_ok(inst, c, maxdeg)]


def _kirchhoff(inst) -> int:
    """Matrix-Baum-Satz: Zahl der Spannbäume = Determinante der Laplace-Matrix ohne erste Zeile und Spalte (Gauß in exakten Brüchen)."""
    n = inst.n
    lap = [[Fraction(0)] * n for _ in range(n)]
    for u, v, _ in inst.edges:
        lap[u][u] += 1
        lap[v][v] += 1
        lap[u][v] -= 1
        lap[v][u] -= 1
    m = [row[1:] for row in lap[1:]]
    size = n - 1
    det = Fraction(1)
    for col in range(size):
        pivot = next((r for r in range(col, size) if m[r][col] != 0), None)
        if pivot is None:
            return 0
        if pivot != col:
            m[col], m[pivot] = m[pivot], m[col]
            det = -det
        det *= m[col][col]
        for r in range(col + 1, size):
            factor = m[r][col] / m[col][col]
            for c in range(col, size):
                m[r][c] -= factor * m[col][c]
    assert det.denominator == 1
    return int(det)


def test_kirchhoff_by_hand_on_a_triangle_and_the_mini_instance(mini):
    from mtr_scenario import Instance

    triangle = Instance(((0.0, 0.0), (1.0, 0.0), (0.0, 1.0)), ((0, 1, 1), (0, 2, 1), (1, 2, 1)))
    assert _kirchhoff(triangle) == 3
    assert _kirchhoff(mini) == 21


def test_tree_count_matches_the_matrix_tree_theorem_on_60_plans():
    for seed in range(60):
        inst = make_instance(4 + seed % 6, seed, hub=bool(seed % 2))
        assert len(A.all_trees(inst)) == _kirchhoff(inst), seed


def test_all_trees_and_the_optimum_match_enumeration_with_and_without_degree_bound():
    for seed in range(40):
        inst = make_instance(5 + seed % 4, seed, hub=bool(seed % 2))
        for maxdeg in (0, 3, 2):
            expected = _trees_by_combinations(inst, maxdeg)
            assert sorted(A.all_trees(inst, maxdeg)) == sorted(expected), (seed, maxdeg)
            best, opts = A.optimum_trees(inst, maxdeg)
            if not expected:
                assert best is None and opts == []
                continue
            costs = [sum(inst.edges[e][2] for e in t) for t in expected]
            assert best == min(costs) and len(opts) == costs.count(min(costs)), (seed, maxdeg)


def test_free_greedy_cost_equals_the_networkx_minimum_spanning_tree():
    nx = pytest.importorskip("networkx")
    for seed in range(60):
        inst = make_instance(5 + seed % 5, seed, hub=bool(seed % 2))
        g = nx.Graph()
        g.add_weighted_edges_from(inst.edges)
        mst = nx.minimum_spanning_tree(g, algorithm="kruskal")
        assert A.cost_of(inst, A.taken(A.greedy_steps(inst))) == mst.size(weight="weight"), seed


def test_shortest_path_tree_gives_every_station_its_networkx_distance():
    nx = pytest.importorskip("networkx")
    for seed in range(40):
        inst = make_instance(5 + seed % 5, seed, hub=bool(seed % 2))
        g = nx.Graph()
        g.add_weighted_edges_from(inst.edges)
        dist = nx.single_source_dijkstra_path_length(g, 0)
        tree = A.shortest_path_tree(inst)
        assert A.check_tree(inst, tree)
        for v in range(inst.n):
            path = A.tree_path(inst, tree, 0, v)
            assert sum(inst.edges[e][2] for e in path) == pytest.approx(dist[v]), (seed, v)


def test_best_forest_cost_per_size_matches_subset_enumeration():
    for seed in range(30):
        inst = make_instance(5 + seed % 3, seed, hub=bool(seed % 2))
        for maxdeg in (0, 2, 3):
            expected = {}
            for r in range(inst.n):
                for c in itertools.combinations(range(inst.m), r):
                    if _acyclic(inst, c) and _degree_ok(inst, c, maxdeg):
                        cost = sum(inst.edges[e][2] for e in c)
                        expected[r] = min(cost, expected.get(r, cost))
            assert A.best_forest_costs(inst, maxdeg) == expected, (seed, maxdeg)


def test_greedy_with_bound_is_always_a_valid_forest_never_cheaper_than_the_optimum():
    for seed in range(60):
        inst = make_instance(5 + seed % 4, seed, hub=bool(seed % 2))
        for maxdeg in (3, 2):
            steps = A.greedy_steps(inst, maxdeg)
            taken = A.taken(steps)
            assert _acyclic(inst, taken) and _degree_ok(inst, taken, maxdeg) and A.check_forest(inst, taken, maxdeg), (seed, maxdeg)
            best, _ = A.optimum_trees(inst, maxdeg)
            if len(taken) == inst.n - 1:
                assert best is not None and A.cost_of(inst, taken) >= best
            assert len(steps) == inst.m                      # ein Schritt je Leitung


def test_local_search_ends_without_an_improving_swap_and_with_a_valid_tree():
    for seed in range(30):
        inst = make_instance(6 + seed % 3, seed, hub=bool(seed % 2))
        for maxdeg in (0, 3, 2):
            start = A.random_start(inst, maxdeg, seed)
            if start is None:
                continue
            end = A.apply_swaps(start, A.local_search(inst, start, maxdeg, "zufällig", seed))
            assert A.check_tree(inst, end, maxdeg) and _acyclic(inst, end) and _degree_ok(inst, end, maxdeg)
            assert A.improving_swaps(inst, end, maxdeg) == []
            if not maxdeg:                                    # ohne Schranke: das Optimum
                assert A.cost_of(inst, end) == A.optimum_trees(inst)[0]
