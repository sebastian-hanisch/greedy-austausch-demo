"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, und jedes Preset zeigt den Effekt, den sein Hilfetext verspricht."""

import mtr_algorithm as A
import mtr_constants as C
import mtr_evaluation as ev
import mtr_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_choices():
    for preset in C.PRESETS.values():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and 0 <= preset["seed"] <= C.SEED_MAX
        assert isinstance(preset["nabe"], bool) and preset["grad"] in C.GRADE_CHOICES


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_standard_preset_greedy_is_optimal_and_all_three_properties_hold():
    s = ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"])
    a = ev.analyse(s)
    assert ev.verdict_optimal(a, s.grad)[0] == "success" and ev.verdict_prefix(ev.prefix_rows(a, s.grad), s.grad)[0] == "success"
    run = ev.swap_run(a, s.grad, "zufällig", C.DEFAULT_START)
    assert not run["stuck"] and len(run["swaps"]) >= 1


def test_nabe_preset_bound_binds_and_greedy_is_worse_and_the_default_start_gets_stuck():
    s = ev.Settings(**C.PRESETS["Billige Nabe, höchstens 3 Leitungen"])
    a = ev.analyse(s)
    assert a.binds and a.is_tree and a.cost > a.opt_cost and ev.verdict_optimal(a, s.grad)[0] == "warning"
    assert ev.verdict_prefix(ev.prefix_rows(a, s.grad), s.grad)[0] == "warning"
    assert ev.swap_run(a, s.grad, "zufällig", C.DEFAULT_START)["stuck"]


def test_path_preset_greedy_finds_no_spanning_tree_although_one_exists():
    s = ev.Settings(**C.PRESETS["Pfad: höchstens 2 Leitungen"])
    a = ev.analyse(s)
    assert not a.is_tree and a.n_trees > 0 and a.opt_cost is not None
    assert max(A.degrees(a.inst, A.taken(a.steps))) <= 2


def test_biggest_preset_has_the_largest_plan_and_greedy_is_optimal():
    s = ev.Settings(**C.PRESETS["Größte Instanz (9 Standorte)"])
    a = ev.analyse(s)
    assert a.inst.n == C.N_MAX and a.cost == a.opt_cost and a.n_trees > 1000


def test_transform_table_uses_the_fixed_instances_and_a_consistent_range():
    rows = ev.transform_table(7, False)
    assert [r["name"] for r in rows] == list(C.TRANSFORMS) and all(r["instances"] == len(C.SWEEP_SEEDS) for r in rows)
    for r in rows:
        assert 0 <= r["kruskal_changed"] <= r["instances"] and 0 <= r["spt_changed"] <= r["instances"]
