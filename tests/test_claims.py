"""Jede Zahl der README („Befunde“) wird hier mit den Funktionen der App nachgerechnet (DEMO-PLAYBOOK §4)."""

import re
from pathlib import Path

import pytest

import mtr_algorithm as A
import mtr_constants as C
import mtr_evaluation as ev

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")


def _preset(name):
    s = ev.Settings(**C.PRESETS[name])
    return s, ev.analyse(s)


def test_standard_case_numbers():
    s, a = _preset("Standardfall (Voreinstellung)")
    assert (s.n, s.seed, s.nabe, s.grad) == (7, 8, False, 0) and a.inst.m == 12
    assert a.n_trees == 180 and a.cost == 156 and a.opt_cost == 156 and a.n_opt == 1
    rows = ev.prefix_rows(a, 0)
    assert len(rows) == 6 and all(r["equal"] for r in rows)
    run = ev.swap_run(a, 0, "zufällig", C.DEFAULT_START)
    assert len(run["swaps"]) == 3 and run["costs"][0] == 220 and run["end_cost"] == 156 and not run["stuck"]


def test_fingerprint_1_table_numbers():
    rows = ev.transform_table(7, False)
    assert len(C.SWEEP_SEEDS) == 40 and min(C.SWEEP_SEEDS) == 100000 and max(C.SWEEP_SEEDS) == 100039
    assert sum(r["instances"] for r in rows) == 200 and sum(r["kruskal_changed"] for r in rows) == 0
    assert {r["name"]: r["spt_changed"] for r in rows} == {"hoch 3": 36, "Logarithmus": 4, "plus 1000": 2, "Exponentialfunktion": 6, "Wurzel": 4}


def test_nabe_preset_numbers():
    s, a = _preset("Billige Nabe, höchstens 3 Leitungen")
    assert a.cost == 126 and a.opt_cost == 115 and a.n_trees == 152
    assert ev.de(ev.percent_over(a.cost, a.opt_cost)) == "9,6"
    rows = ev.prefix_rows(a, 3)
    assert [r["k"] for r in rows if not r["equal"]] == [5, 6]
    assert rows[4]["greedy"] == 86 and rows[4]["best"] == 76
    run = ev.swap_run(a, 3, "zufällig", C.DEFAULT_START)
    assert len(run["swaps"]) == 5 and run["end_cost"] == 132 and run["opt_cost"] == 115 and run["stuck"]
    best = ev.swap_run(a, 3, "bester", C.DEFAULT_START)
    assert len(best["swaps"]) == 3 and best["end_cost"] == 115 and not best["stuck"]


def test_path_preset_numbers():
    s, a = _preset("Pfad: höchstens 2 Leitungen")
    assert (s.n, s.seed, s.nabe, s.grad) == (7, 8, False, 2)
    assert len(a.tree) == 5 and a.inst.n - 1 == 6 and not a.is_tree and a.n_trees == 24 and a.opt_cost == 162


def test_biggest_preset_numbers():
    s, a = _preset("Größte Instanz (9 Standorte)")
    assert a.n_trees == 1160 and a.opt_cost == 127 and a.n_opt == 2 and a.cost == 127


@pytest.fixture(scope="module")
def stats_plain():
    return {r["grad"]: r for r in ev.grad_statistics(7, False)}


@pytest.fixture(scope="module")
def stats_hub():
    return {r["grad"]: r for r in ev.grad_statistics(7, True)}


def test_experiment_4_without_nabe(stats_plain):
    free, g3, g2 = stats_plain[0], stats_plain[3], stats_plain[2]
    assert (free["greedy_worse"], free["greedy_none"], free["stuck"], free["runs"]) == (0, 0, 0, 120)
    assert (g3["instances"], g3["binds"], g3["greedy_worse"], g3["greedy_none"], g3["stuck"], g3["runs"]) == (40, 0, 0, 0, 1, 120)
    assert (g2["instances"], g2["no_tree"], g2["binds"], g2["greedy_none"], g2["greedy_worse"], g2["stuck"], g2["runs"]) == (37, 3, 30, 21, 1, 56, 111)


def test_experiment_4_with_nabe(stats_hub):
    free, g3, g2 = stats_hub[0], stats_hub[3], stats_hub[2]
    assert (free["greedy_worse"], free["greedy_none"], free["stuck"]) == (0, 0, 0)
    assert (g3["instances"], g3["binds"], g3["greedy_worse"], g3["greedy_none"], g3["stuck"], g3["runs"]) == (40, 37, 20, 5, 44, 120)
    assert (g2["instances"], g2["binds"], g2["greedy_worse"], g2["greedy_none"], g2["stuck"], g2["runs"]) == (37, 37, 6, 22, 60, 111)


def test_experiment_5_numbers():
    rows = {r["label"]: r for r in ev.axiom_statistics()}
    assert len(C.AXIOM_SEEDS) == 12 and C.AXIOM_N == 7 and C.AXIOM_PAIRS == 20
    tree, g3, path = rows["Spannbäume"], rows["Spannbäume mit höchstens 3 Leitungen je Standort"], rows["Pfade (höchstens 2 Leitungen je Standort)"]
    assert (tree["triples"], tree["fail"], tree["sym_fail"]) == (694, 0, 0)
    assert (g3["triples"], g3["fail"], g3["sym_fail"]) == (654, 44, 152)
    assert (path["triples"], path["fail"], path["sym_fail"]) == (616, 356, 546)
    assert ev.de(100.0 * 44 / 654) == "6,7" and ev.de(100.0 * 152 / 654) == "23,2"
    assert ev.de(100.0 * 356 / 616) == "57,8" and ev.de(100.0 * 546 / 616) == "88,6"


def test_model_statements():
    for n in range(C.N_MIN, C.N_MAX + 1):
        assert ev.analyse(ev.Settings(n=n)).inst.m == min(n * (n - 1) // 2, 2 * n - 2)
    assert ev.analyse(ev.Settings(n=C.N_MAX)).inst.m == 16
    assert C.HUB_FACTOR == 0.4 and C.COST_SCALE == 100 and C.GRADE_CHOICES == (0, 3, 2)


def test_readme_names_every_checked_number():
    for needle in ("**156**", "**126**", "**115**", "**9,6 %**", "152 Spannbäume", "86 statt 76", "**132**", "**5 von 6**", "**24**", "**36** von 40",
                   "**37** von 40", "**20**", "**44** von 120", "**694**", "44 von 654 (6,7 %)", "152 (23,2 %)", "356 von 616 (57,8 %)", "546 (88,6 %)",
                   "1160 Spannbäume", "**127**", "0 von 200", "Seeds 100000 bis 100039"):
        assert needle in README, needle


def test_readme_has_no_decimal_points_in_prose_numbers():
    table = README.split("## Befunde (gemessen, keine Behauptungen)")[1].split("## Ehrliche Grenzen")[0]
    assert not re.search(r"\d\.\d", table)
