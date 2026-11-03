"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): n = 1, n = 2, Gleichstand, inklusive Grenzen, Entartungen."""

import pytest

import mtr_algorithm as A
import mtr_constants as C
import mtr_evaluation as ev
from mtr_scenario import Instance, make_instance


def test_a_single_station_needs_no_leitung():
    inst = make_instance(1, 5)
    assert inst.n == 1 and inst.m == 0
    a = ev.analyse(ev.Settings(n=1, seed=5))
    assert a.tree == () and a.is_tree and a.cost == 0 and a.n_trees == 1 and a.opt_cost == 0
    assert ev.verdict_optimal(a, 0)[0] == "success"
    assert ev.prefix_rows(a, 0) == [] and ev.verdict_prefix([], 0)[0] == "info"
    run = ev.swap_run(a, 0, "zufällig", 0)
    assert run["swaps"] == [] and not run["stuck"]


def test_exactly_two_stations_have_one_leitung_and_one_tree():
    inst = make_instance(2, 5)
    assert inst.m == 1
    assert A.taken(A.greedy_steps(inst)) == (0,)
    assert A.all_trees(inst) == [(0,)]
    a = ev.analyse(ev.Settings(n=2, seed=5))
    assert a.is_tree and a.n_trees == 1 and a.n_opt == 1
    assert "nur einen Spannbaum" in ev.verdict_optimal(a, 0)[1]
    assert A.all_trees(inst, 1) == [(0,)]                    # Grad 1 reicht für zwei Standorte (inklusive Grenze)


def test_three_stations_form_a_triangle_and_degree_two_is_enough():
    inst = make_instance(3, 5)
    assert inst.m == 3 and len(A.all_trees(inst)) == 3 and len(A.all_trees(inst, 2)) == 3


def test_all_equal_costs_every_tree_is_optimal_and_swaps_never_move():
    inst = Instance(((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)), ((0, 1, 5), (0, 2, 5), (1, 3, 5), (2, 3, 5), (1, 2, 5)))
    trees = A.all_trees(inst)
    best, opts = A.optimum_trees(inst)
    assert best == 15 and len(opts) == len(trees)
    assert A.taken(A.greedy_steps(inst)) == (0, 1, 2)       # bei Gleichstand gewinnt der kleinere Index
    for t in trees:
        assert A.improving_swaps(inst, t) == []
        assert A.local_search(inst, t) == []


def test_star_with_degree_bound_two_has_no_spanning_tree():
    star = Instance(((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)), ((0, 1, 1), (0, 2, 1), (0, 3, 1)))
    assert A.all_trees(star, 2) == [] and A.optimum_trees(star, 2) == (None, []) and A.random_start(star, 2, 0) is None
    a = ev.analyse(ev.Settings(n=4, seed=1))                  # beliebiger Plan, nur um die Art der Verdikte zu prüfen
    assert ev.verdict_optimal(ev.Analysis(star, (), (), (), False, None, 3, True, 0, None, 0), 2)[0] == "info"
    assert a.n_trees >= 1


def test_degree_bound_one_allows_two_stations_but_not_a_path_of_three():
    path = Instance(((0.0, 0.0), (1.0, 0.0), (2.0, 0.0)), ((0, 1, 1), (1, 2, 1)))
    assert A.all_trees(path, 1) == []                         # Grad 1: der mittlere Standort hat zwei Leitungen
    assert A.all_trees(path, 2) == [(0, 1)]


def test_make_instance_rejects_sizes_outside_the_letters():
    for n in (0, 27):
        with pytest.raises(ValueError):
            make_instance(n, 1)
    assert make_instance(26, 1).n == 26


def test_tree_path_raises_for_disconnected_edges(mini):
    with pytest.raises(ValueError):
        A.tree_path(mini, (6,), 0, 4)                          # nur D-E: A ist nicht erreichbar


def test_slider_bounds_are_inclusive_and_inside_the_letters():
    assert C.N_MIN <= C.DEFAULT_N <= C.N_MAX
    for n in (C.N_MIN, C.N_MAX):
        a = ev.analyse(ev.Settings(n=n, seed=3, nabe=True, grad=3))
        assert a.inst.n == n and a.n_trees >= 0
    assert C.GRADE_OFF in C.GRADE_CHOICES and set(C.GRADE_CHOICES) == {0, 2, 3}


def test_improving_swaps_with_costs_equal_are_not_counted(mini):
    equal = Instance(mini.points, tuple((u, v, 1) for u, v, _ in mini.edges))
    for t in A.all_trees(equal):
        assert A.improving_swaps(equal, t) == []
