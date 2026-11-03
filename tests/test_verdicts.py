"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jeder Zweig der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen, nicht Seeds."""

import mtr_constants as C
import mtr_evaluation as ev
from mtr_scenario import Instance

INST = Instance(((0.5, 0.5), (0.2, 0.8), (0.8, 0.8), (0.2, 0.2), (0.8, 0.2)), ((0, 1, 4), (0, 2, 1), (1, 2, 2), (1, 3, 5), (2, 3, 8)))


def _a(**kw):
    base = dict(inst=INST, steps=(), free_steps=(), tree=(1, 2, 4, 3), is_tree=True, cost=11, free_cost=11, binds=False, n_trees=21, opt_cost=11, n_opt=1)
    base.update(kw)
    return ev.Analysis(**base)


def test_formatting_helpers():
    assert ev.de(16.666, 1) == "16,7" and ev.de(3.0, 0) == "3"
    assert ev.kosten(11.0) == "11" and ev.kosten(11) == "11" and ev.kosten(11.5) == "11,5"
    assert ev.grade_label(0) == "keine Gradschranke" and ev.grade_label(3) == "höchstens 3 Leitungen je Standort"
    assert ev.nach_tausch(0) == "Am Start" and ev.nach_tausch(1) == "Nach 1 Tausch" and ev.nach_tausch(4) == "Nach 4 Tauschen"


def test_percent_over_uses_the_reference_as_base():
    assert ev.percent_over(7, 6) == 100.0 / 6
    assert ev.percent_over(5, 0) == 0.0 and ev.percent_over(5, -1) == 0.0


def test_optimal_without_tree_is_an_info_that_names_the_bound():
    kind, text = ev.verdict_optimal(_a(n_trees=0, is_tree=False, cost=None, opt_cost=None, n_opt=0), 3)
    assert kind == "info" and "höchstens 3 Leitungen je Standort" in text and "keinen Spannbaum" in text


def test_greedy_without_tree_names_the_missing_edges_and_the_best_tree():
    kind, text = ev.verdict_optimal(_a(is_tree=False, tree=(0, 1, 4), cost=None, opt_cost=10, n_trees=2, n_opt=2), 2)
    assert kind == "warning"
    assert "nach 3 von 4 nötigen Leitungen" in text and "**keinen** Spannbaum" in text and "obwohl es 2 Spannbäume gibt" in text and "kostet 10" in text
    assert "obwohl es einen Spannbaum gibt" in ev.verdict_optimal(_a(is_tree=False, tree=(0, 1, 4), cost=None, opt_cost=10, n_trees=1), 2)[1]


def test_optimal_with_binding_bound_is_a_coincidence_info():
    kind, text = ev.verdict_optimal(_a(binds=True), 3)
    assert kind == "info" and "Die Schranke bindet" in text and "(11)" in text and "Zufall" in text


def test_optimal_success_counts_the_trees_and_the_optimal_ones():
    kind, text = ev.verdict_optimal(_a(), 0)
    assert kind == "success" and "Kosten 11" in text and "Unter 21 Spannbäumen ist genau einer optimal, und Greedy findet ihn." in text
    assert "Die Schranke bindet hier nicht" not in text
    assert "Unter 21 Spannbäumen sind 2 optimal, Greedy findet einen davon." in ev.verdict_optimal(_a(n_opt=2), 0)[1]
    assert "nur einen Spannbaum" in ev.verdict_optimal(_a(n_trees=1), 0)[1]
    assert ev.verdict_optimal(_a(), 3)[1].endswith("Die Schranke bindet hier nicht.")


def test_greedy_worse_than_the_optimum_names_both_costs_and_the_percentage_over_the_best():
    kind, text = ev.verdict_optimal(_a(cost=7, opt_cost=6, n_trees=5, n_opt=2), 2)
    assert kind == "warning" and "Kosten 7" in text and "Optimum ist 6" in text and "**16,7 %** über dem besten (von 5 Spannbäumen)" in text


def test_transform_verdict_counts_comparisons_and_the_range_of_the_shortest_path_tree():
    rows = [{"name": "a", "instances": 40, "kruskal_changed": 0, "spt_changed": 3}, {"name": "b", "instances": 40, "kruskal_changed": 0, "spt_changed": 17}]
    kind, text = ev.verdict_transform(rows)
    assert kind == "success" and "**keiner** der 2 Umrechnungen auf 40 festen Plänen (80 Vergleiche)" in text and "in 3 bis 17 von 40 Plänen" in text
    rows[1]["kruskal_changed"] = 2
    kind, text = ev.verdict_transform(rows)
    assert kind == "warning" and "in 2 von 80 Vergleichen" in text


def test_prefix_verdict_all_equal_names_the_bound():
    rows = [{"k": k, "greedy": k, "best": k, "equal": True} for k in (1, 2, 3)]
    assert ev.verdict_prefix(rows, 0) == ("success", "Für **alle** 3 Größen k sind die ersten k Kanten von Greedy der billigste Wald mit k Kanten (keine Gradschranke).")
    assert "(höchstens 3 Leitungen je Standort)" in ev.verdict_prefix(rows, 3)[1]


def test_prefix_verdict_names_the_failing_sizes_and_the_first_failure():
    rows = [
        {"k": 1, "greedy": 1, "best": 1, "equal": True},
        {"k": 2, "greedy": 5, "best": 4, "equal": False},
        {"k": 3, "greedy": None, "best": 6, "equal": False},
    ]
    kind, text = ev.verdict_prefix(rows, 3)
    assert kind == "warning" and "Bei 2 von 3 Größen (k = 2, 3) ist Greedy nicht optimal" in text and "Erstes Versagen bei k = 2: Greedy hat 5, der beste Wald 4." in text
    rows2 = [{"k": 1, "greedy": None, "best": 1, "equal": False}]
    assert "Greedy hat zu diesem k keine Kanten mehr genommen" in ev.verdict_prefix(rows2, 2)[1]


def test_swap_verdicts():
    assert ev.verdict_swaps(None, 3)[0] == "info" and "höchstens 3 Leitungen je Standort" in ev.verdict_swaps(None, 3)[1]
    ok = {"swaps": [(1, 2), (3, 4)], "end_cost": 11, "opt_cost": 11, "stuck": False, "distance": 2}
    kind, text = ev.verdict_swaps(ok, 0)
    assert kind == "success" and text.startswith("Nach 2 Tauschen ist kein verbessernder Tausch mehr möglich") and "(11) sind das Optimum" in text and "2 Kanten vom nächsten" in text
    one = dict(ok, swaps=[(1, 2)], distance=1)
    assert "Nach 1 Tausch ist" in ev.verdict_swaps(one, 0)[1] and "eine Kante vom nächsten" in ev.verdict_swaps(one, 0)[1]
    zero = dict(ok, swaps=[], distance=0)
    assert ev.verdict_swaps(zero, 0)[1].startswith("Schon der Startbaum erlaubt keinen") and "schon optimal" in ev.verdict_swaps(zero, 0)[1]
    stuck = {"swaps": [(1, 2)], "end_cost": 14, "opt_cost": 11, "stuck": True, "distance": 3}
    kind, text = ev.verdict_swaps(stuck, 3)
    assert kind == "warning" and "Nach 1 Tausch gibt es keinen erlaubten" in text and "Kosten 14 liegen über dem Optimum 11" in text


def test_grad_verdict_reports_counts_per_bound_and_flags_a_free_deviation():
    rows = [
        {"grad": 0, "instances": 40, "no_tree": 0, "binds": 0, "greedy_worse": 0, "greedy_none": 0, "runs": 120, "stuck": 0},
        {"grad": 3, "instances": 40, "no_tree": 0, "binds": 37, "greedy_worse": 20, "greedy_none": 5, "runs": 120, "stuck": 44},
        {"grad": 2, "instances": 37, "no_tree": 3, "binds": 37, "greedy_worse": 6, "greedy_none": 22, "runs": 111, "stuck": 60},
    ]
    kind, text = ev.verdict_grad(rows)
    assert kind == "info" and text.startswith("Ohne Schranke: 0 Abweichungen bei 40 Plänen und 120 Läufen.")
    assert "die Schranke bindet in 37 von 40 Plänen, Greedy ist in 20 nicht optimal und findet in 5 keinen Spannbaum, die Tausch-Lokalsuche bleibt in 44 von 120 Läufen" in text
    assert "höchstens 2 Leitungen je Standort**: die Schranke bindet in 37 von 37 Plänen" in text
    rows[0]["stuck"] = 1
    assert ev.verdict_grad(rows)[0] == "warning"


def test_axiom_verdict_names_the_tripel_and_the_percentages():
    rows = [
        {"label": "Spannbäume", "triples": 694, "fail": 0, "sym_fail": 0},
        {"label": "Grad 3", "triples": 654, "fail": 44, "sym_fail": 152},
    ]
    kind, text = ev.verdict_axiom(rows)
    assert kind == "info" and "jedes der 694 Tripel" in text and "Grad 3: 6,7 % ohne Austauschpartner, 23,2 % ohne symmetrischen" in text
    rows[0]["fail"] = 1
    assert ev.verdict_axiom(rows)[0] == "warning"


def test_sweep_sizes_are_the_documented_ones():
    assert len(C.SWEEP_SEEDS) == 40 and len(C.AXIOM_SEEDS) == 12 and C.AXIOM_PAIRS == 20 and C.LOCAL_STARTS == 3
