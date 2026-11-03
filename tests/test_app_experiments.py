"""AppTest: Experimente, Spielwiese, Permalink, Schritt-Regler und PDF (DEMO-PLAYBOOK §3, §5)."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import mtr_algorithm as A
import mtr_constants as C
import mtr_evaluation as ev
from mtr_pdf_export import build_pdf

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _app(params=None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    for key, value in (params or {}).items():
        at.query_params[key] = value
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return [m.value for m in list(at.success) + list(at.info) + list(at.warning) + list(at.error)]


def _click_preset(at, name):
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]


def test_kernfrage_verdict_matches_each_preset():
    expected = {
        "Standardfall (Voreinstellung)": "Greedy trifft das Optimum: Kosten 156",
        "Billige Nabe, höchstens 3 Leitungen": "Greedy liefert Kosten 126, das Optimum ist 115",
        "Pfad: höchstens 2 Leitungen": "findet **keinen** Spannbaum",
        "Größte Instanz (9 Standorte)": "Greedy trifft das Optimum: Kosten 127",
    }
    at = _app()
    for name, needle in expected.items():
        _click_preset(at, name)
        assert any(needle in t for t in _texts(at)), name


def test_experiment_1_selection_shows_the_current_plan():
    at = _app()
    for name in C.TRANSFORMS:
        at.selectbox(key="e1_transform").set_value(name).run()
        assert not at.exception
        assert [m.value for m in at.metric if m.label == "Kruskal-Baum auf diesem Plan"] == ["unverändert"]


def test_experiment_4_button_shows_a_table_and_the_verdict():
    at = _app()
    assert not any("Ohne Schranke: 0 Abweichungen" in t for t in _texts(at))
    at.button(key="e4_run").click().run()
    assert not at.exception
    assert any("Ohne Schranke: 0 Abweichungen bei 40 Plänen und 120 Läufen" in t for t in _texts(at))
    table = at.dataframe[-1].value if at.dataframe else None
    assert table is not None


def test_experiment_5_button_shows_the_numbers():
    at = _app()
    at.button(key="e5_run").click().run()
    assert not at.exception
    assert any("jedes der 694 Tripel" in t for t in _texts(at))


def test_experiment_3_rules_and_new_start():
    at = _app(dict(nabe="1", grad="3"))
    assert at.session_state["e3_seed"] == C.DEFAULT_START
    assert any("ein lokales Optimum, das nicht das beste ist" in t for t in _texts(at))   # Startbaum 1 bleibt hängen
    at.selectbox(key="e3_rule").set_value("bester").run()
    assert not at.exception and any("sind das Optimum" in t for t in _texts(at))
    at.button(key="e3_new").click().run()
    assert at.session_state["e3_seed"] == C.DEFAULT_START + 1 and not at.exception


def test_experiment_3_step_slider_clamps_when_the_run_gets_shorter():
    at = _app()
    slider = at.slider(key="e3_step")
    slider.set_value(slider.max).run()
    assert not at.exception
    at.button(key="e3_new").click().run()
    assert not at.exception


def test_greedy_step_slider_describes_each_step():
    at = _app()
    for step in (0, 1, 5, 12):
        at.slider(key="greedy_step").set_value(step).run()
        assert not at.exception
    assert any(c.value.startswith("Schritt 12:") for c in at.caption)
    at.slider(key="greedy_step").set_value(0).run()
    assert any(c.value.startswith("Noch keine Leitung angesehen") for c in at.caption)


def test_greedy_step_is_clamped_when_the_plan_gets_smaller():
    at = _app(dict(n="9"))
    assert at.slider(key="greedy_step").max == 16
    at.slider(key="greedy_step").set_value(16).run()
    at.sidebar.slider(key="n_slider").set_value(6).run()
    assert not at.exception and at.slider(key="greedy_step").value == 10 == at.slider(key="greedy_step").max


def test_permalink_loads_valid_values_and_ignores_invalid_choices():
    at = _app(dict(n="8", seed="3", nabe="1", grad="2"))
    assert at.sidebar.slider(key="n_slider").value == 8 and at.sidebar.number_input(key="seed_input").value == 3
    assert at.sidebar.toggle(key="nabe_toggle").value is True and at.sidebar.selectbox(key="grad_select").value == 2
    bad = _app(dict(n="99", seed="-4", nabe="vielleicht", grad="1"))
    assert bad.sidebar.slider(key="n_slider").value == C.N_MAX and bad.sidebar.number_input(key="seed_input").value == 0
    assert bad.sidebar.toggle(key="nabe_toggle").value is False and bad.sidebar.selectbox(key="grad_select").value == C.GRADE_OFF
    garbage = _app(dict(n="abc", grad="x"))
    assert garbage.sidebar.slider(key="n_slider").value == C.DEFAULT_N and garbage.sidebar.selectbox(key="grad_select").value == C.GRADE_OFF


def test_address_line_mirrors_the_settings():
    at = _app(dict(nabe="1", grad="3"))
    assert at.query_params["grad"] == ["3"] or at.query_params["grad"] == "3"


def test_playground_swap_executes_an_improving_swap():
    at = _app()
    tree = at.session_state["play_tree"]
    s = ev.Settings()
    inst = ev.analyse(s).inst
    e, f = A.improving_swaps(inst, tree, 0)[0]
    before = A.cost_of(inst, tree)
    at.selectbox(key="play_in").set_value(e).run()
    at.selectbox(key="play_out").set_value(f).run()
    at.button(key="play_do").click().run()
    assert not at.exception
    new = at.session_state["play_tree"]
    assert new == A.apply_swap(tree, e, f) and A.cost_of(inst, new) < before
    assert any("Kosten" in t and "→" in t for t in _texts(at))


def test_playground_rejects_a_swap_that_breaks_the_degree_bound():
    at = _app(dict(nabe="1", grad="3"))
    tree = at.session_state["play_tree"]
    inst = ev.analyse(ev.Settings(nabe=True, grad=3)).inst
    bad = None
    for e in range(inst.m):
        if e in tree:
            continue
        for f in A.cycle_edges(inst, tree, e):
            if not A.swap_ok(inst, tree, e, f, 3):
                bad = (e, f)
    if bad is None:
        pytest.skip("kein verbotener Tausch auf diesem Startbaum")
    at.selectbox(key="play_in").set_value(bad[0]).run()
    at.selectbox(key="play_out").set_value(bad[1]).run()
    at.button(key="play_do").click().run()
    assert not at.exception and at.session_state["play_tree"] == tree
    assert any("nicht erlaubt" in t for t in _texts(at))


def test_playground_new_tree_and_reset_on_other_settings():
    at = _app()
    first = at.session_state["play_tree"]
    at.button(key="play_new").click().run()
    assert not at.exception and at.session_state["play_seed"] == 1
    at.sidebar.number_input(key="seed_input").set_value(9).run()
    assert not at.exception and at.session_state["play_tree"] != first


def test_playground_without_spanning_tree_shows_info():
    no_tree = [seed for seed in C.SWEEP_SEEDS if ev.analyse(ev.Settings(n=7, seed=seed, nabe=False, grad=2)).n_trees == 0]
    assert len(no_tree) == 3                                  # die 3 Pläne ohne Spannbaum aus Experiment 4 (ohne Nabe, Schranke 2)
    at = _app(dict(n="7", seed=str(no_tree[0]), grad="2"))
    assert any("keinen Spannbaum" in t for t in _texts(at))
    assert any("Spannbaum" in i.value for i in at.info)


def test_pdf_button_makes_a_download():
    at = _app()
    at.button(key="pdf_make").click().run()
    assert not at.exception
    assert "pdf_made" in at.session_state and at.session_state["pdf_made"][1][:4] == b"%PDF"


def test_pdf_builds_for_every_preset_and_every_bound():
    for name, preset in C.PRESETS.items():
        s = ev.Settings(**preset)
        assert build_pdf(ev.analyse(s), s)[:4] == b"%PDF", name
    for grad in C.GRADE_CHOICES:
        s = ev.Settings(n=6, seed=2, nabe=True, grad=grad)
        assert build_pdf(ev.analyse(s), s)[:4] == b"%PDF"


def test_every_slider_and_selection_extreme_combination_does_not_raise():
    for n in (C.N_MIN, C.N_MAX):
        for nabe in ("0", "1"):
            for grad in ("0", "2", "3"):
                at = _app(dict(n=str(n), nabe=nabe, grad=grad))
                at.button(key="e4_run").click().run()
                at.button(key="e5_run").click().run()
                assert not at.exception, (n, nabe, grad)
