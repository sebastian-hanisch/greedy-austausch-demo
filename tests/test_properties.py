"""Eigenschaftstests (ORACLE-PLAYBOOK §5): Aussagen, die für jede Instanz gelten müssen, auf festen Zufallsinstanzen.

Hier stehen die drei Fingerabdrücke von Greedy, die Invarianz gegen die Eingabe-Reihenfolge und die Reproduzierbarkeit über Prozesse (Hash-Reihenfolge)."""

import os
import random
import subprocess
import sys
from pathlib import Path

import mtr_algorithm as A
import mtr_constants as C
import mtr_evaluation as ev
from mtr_scenario import Instance, make_instance

ROOT = Path(__file__).resolve().parent.parent


def _plans(count=40, lo=5, hi=9):
    for seed in range(count):
        yield seed, make_instance(lo + seed % (hi - lo + 1), seed, hub=bool(seed % 2))


def test_fingerprint_1_only_the_order_of_the_costs_matters():
    for seed, inst in _plans():
        base = frozenset(A.taken(A.greedy_steps(inst)))
        for name in C.TRANSFORMS:
            assert frozenset(A.taken(A.greedy_steps(A.transformed(inst, name)))) == base, (seed, name)


def test_fingerprint_1_holds_for_a_random_strictly_increasing_map_as_well():
    rng = random.Random(4)
    for seed, inst in _plans(30):
        base = frozenset(A.taken(A.greedy_steps(inst)))
        values = sorted({c for _, _, c in inst.edges})
        new = dict(zip(values, sorted(rng.uniform(0, 1000) for _ in values)))
        mapped = Instance(inst.points, tuple((u, v, new[c]) for u, v, c in inst.edges))
        assert frozenset(A.taken(A.greedy_steps(mapped))) == base, seed


def test_fingerprint_2_the_first_k_edges_are_the_cheapest_forest_of_size_k_without_bound():
    for seed, inst in _plans(40, 5, 8):
        rows = ev.prefix_rows(ev.analyse(ev.Settings(inst.n, seed, bool(seed % 2), 0)), 0)
        assert all(r["equal"] for r in rows), seed
        assert [r["k"] for r in rows] == list(range(1, inst.n))


def test_fingerprint_3_swap_search_ends_in_the_optimum_without_bound_and_from_every_start_rule():
    for seed, inst in _plans(30, 6, 8):
        best = A.optimum_trees(inst)[0]
        start = A.random_start(inst, 0, seed)
        for rule in ("zufällig", "bester"):
            assert A.cost_of(inst, A.apply_swaps(start, A.local_search(inst, start, 0, rule, seed))) == best, (seed, rule)


def test_exchange_property_of_spanning_trees_has_no_exception_in_a_sample():
    for seed, inst in _plans(20, 5, 7):
        trees = A.all_trees(inst)
        triples, fail, sym_fail = A.exchange_counts(inst, trees, 15, seed)
        assert triples > 0 and fail == 0 and sym_fail == 0, seed


def test_exchange_property_fails_for_paths_somewhere():
    total = fail = 0
    for seed in range(C.AXIOM_SEEDS[0], C.AXIOM_SEEDS[0] + 6):
        inst = make_instance(C.AXIOM_N, seed)
        t, f, _ = A.exchange_counts(inst, A.all_trees(inst, 2), 10, seed)
        total += t
        fail += f
    assert total > 0 and fail > 0


def test_greedy_tree_does_not_depend_on_the_edge_order_in_the_input_for_distinct_costs():
    rng = random.Random(9)
    for seed, inst in _plans(30, 5, 8):
        costs = list(range(1, inst.m + 1))
        rng.shuffle(costs)
        keyed = [(u, v, c) for (u, v, _), c in zip(inst.edges, costs)]
        a = Instance(inst.points, tuple(keyed))
        shuffled = keyed[:]
        rng.shuffle(shuffled)
        b = Instance(inst.points, tuple(shuffled))
        ga = {(a.edges[e][0], a.edges[e][1]) for e in A.taken(A.greedy_steps(a))}
        gb = {(b.edges[e][0], b.edges[e][1]) for e in A.taken(A.greedy_steps(b))}
        assert ga == gb, seed


def test_adding_a_bound_never_makes_the_optimum_cheaper():
    for seed, inst in _plans(30, 6, 8):
        free = A.optimum_trees(inst)[0]
        for maxdeg in (3, 2):
            best = A.optimum_trees(inst, maxdeg)[0]
            assert best is None or best >= free


def test_the_free_greedy_tree_always_satisfies_a_bound_it_already_keeps():
    for seed, inst in _plans(40, 5, 9):
        free = A.taken(A.greedy_steps(inst))
        top = max(A.degrees(inst, free))
        for maxdeg in (2, 3):
            if top <= maxdeg:
                assert A.taken(A.greedy_steps(inst, maxdeg)) == free, (seed, maxdeg)


def test_statistics_are_identical_in_two_processes_with_different_hash_seeds():
    code = (
        "import sys; sys.path.insert(0, %r); import mtr_evaluation as ev; "
        "r = ev.grad_statistics(6, True, seeds=range(100000, 100006), starts=2); a = ev.axiom_statistics(seeds=range(100100, 100103), pairs=5); "
        "print(r); print(a); print(ev.transform_table(6, True, seeds=range(100000, 100006)))"
    ) % str(ROOT)
    outs = []
    for hash_seed in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed)
        outs.append(subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=120, check=True).stdout)
    assert outs[0] == outs[1] and outs[0].strip()
