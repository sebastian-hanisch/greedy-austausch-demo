"""Greedy und Tausch: warum die Regel gewinnt - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 1 der Reihe „Matroide und Submodularität“ (Bereich Kombinatorik). Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import mtr_algorithm as A
import mtr_constants as C
from mtr_evaluation import (
    Settings,
    analyse,
    axiom_statistics,
    de,
    edge_table,
    grad_statistics,
    grade_label,
    kosten,
    nach_tausch,
    play_status,
    prefix_rows,
    swap_run,
    transform_current,
    transform_table,
    verdict_axiom,
    verdict_grad,
    verdict_optimal,
    verdict_prefix,
    verdict_swaps,
    verdict_transform,
)
from mtr_layout import dunkles_design, kopf_css
from mtr_pdf_export import build_pdf
from mtr_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from mtr_visualization import build_map, build_prefix_chart, build_swap_chart

st.set_page_config(page_title="Greedy und Tausch – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _prefix(settings):
    return prefix_rows(analyse(settings), settings.grad)


@st.cache_data(show_spinner=False)
def _swap_run(settings, rule, seed):
    return swap_run(analyse(settings), settings.grad, rule, seed)


@st.cache_data(show_spinner=False)
def _transform_table(n, nabe):
    return transform_table(n, nabe)


@st.cache_data(show_spinner="Mit und ohne Gradschranke auf 40 festen Plänen messen …")
def _grad_stats(n, nabe):
    return grad_statistics(n, nabe)


@st.cache_data(show_spinner=False)
def _axiom_stats():
    return axiom_statistics()


def _grade_name(g):
    return "aus" if g == C.GRADE_OFF else f"höchstens {g}"


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in mtr_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🌳 Greedy und Tausch: warum die Regel gewinnt")
st.markdown(
    """
Ein Leitungsnetz soll alle Standorte verbinden, so billig wie möglich. **Greedy** ordnet die möglichen Leitungen nach Kosten und nimmt jede, die keinen Kreis schließt (**Kruskal**). Auf dem Spannbaum ist das optimal, und zwar auf eine Art, die man **prüfen** kann: Die Regel kennt nur die **Reihenfolge** der Kosten, sie ist für **jede** Größe gleichzeitig optimal, und **Tauschen** führt von jedem Baum zum Optimum. Kommt eine einzige Nebenbedingung dazu (höchstens drei Leitungen je Standort, an einem Depot, das sonst viele Leitungen wollte), bleibt die Regel dieselbe, doch diese Eigenschaften können kippen.

Dies ist das **erste Stück** der Reihe „Matroide und Submodularität“. Weiter unten: fünf Experimente (🔬), eine **Spielwiese** zum Tauschen von Hand, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert Greedy und Tausch", expanded=True):
    st.markdown(
        """
1. **Greedy (Kruskal):** Alle möglichen Leitungen nach Kosten ordnen (bei gleichen Kosten gewinnt die kleinere Nummer). Der Reihe nach jede Leitung nehmen, die keinen **Kreis** schließt.
2. **Mit Gradschranke:** Zusätzlich eine Leitung auslassen, wenn an einem Standort dann mehr als die erlaubten Leitungen enden. Die Regel bleibt dieselbe, nur die Zulässigkeit ist enger.
3. **Tausch:** Legt man zu einem Spannbaum eine weitere Leitung dazu, entsteht genau **ein Kreis**. Entfernt man eine **teurere** Leitung dieses Kreises, bleibt es ein Spannbaum, und er wird billiger.
4. **Warum das hier funktioniert:** Bei Spannbäumen findet jeder Tausch einen Partner (Experiment 5 zählt das an einer Stichprobe nach). Diese Tausch-Eigenschaft ist bekanntermaßen der Grund, dass es keine falschen lokalen Optima gibt. Wie sie heißt und was sie trägt, zeigt Stück 3 (das Matroid).
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Plan**")
    n = st.slider("Standorte (mit Depot A)", *bounds("n_slider"), key="n_slider", help="Wie viele Standorte der Plan hat. Bis 9, damit das Aufzählen aller Spannbäume schnell bleibt.")
    seed = st.number_input("Zufalls-Seed des Plans", *bounds("seed_input"), key="seed_input", step=1)
    nabe = st.toggle("Billige Nabe", key="nabe_toggle", help="Leitungen am Depot (Standort A) kosten nur 40 % der Entfernung: der billigste Baum will dann viele Leitungen am Depot.")
    st.button("🎲 Neuen Plan generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**Nebenbedingung**")
    grad = st.selectbox(
        "Leitungen je Standort", C.GRADE_CHOICES, key="grad_select", format_func=_grade_name,
        help="Höchstzahl der Leitungen, die an einem Standort enden dürfen. 'aus' ist das gewöhnliche Spannbaum-Problem.",
    )

sync_query_params({"n_slider": int(n), "seed_input": int(seed), "nabe_toggle": bool(nabe), "grad_select": int(grad)})

settings = Settings(int(n), int(seed), bool(nabe), int(grad))
a = _analysis(settings)
inst = a.inst

# --- Greedy in Aktion -----------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Greedy in Aktion")
if st.session_state.get("greedy_step", inst.m) > inst.m:
    st.session_state["greedy_step"] = inst.m
step = st.slider("Schritt (Leitungen in Kostenreihenfolge)", 0, inst.m, inst.m, key="greedy_step", help="Wie viele der möglichen Leitungen Greedy schon angesehen hat.")
seen = a.steps[:step]
col_map, col_table = st.columns([3, 2])
with col_map:
    st.plotly_chart(
        build_map(inst, taken=[s.edge for s in seen if s.status == "genommen"], rejected=[s.edge for s in seen if s.status != "genommen"], height=500),
        width="stretch", key="main_map",
    )
with col_table:
    st.markdown("**Alle Entscheidungen von Greedy**")
    st.dataframe(edge_table(a), hide_index=True, width="stretch", height=460)
if step:
    s = a.steps[step - 1]
    u, v, c = inst.edges[s.edge]
    why = {"genommen": "genommen", "Kreis": "verworfen: sie schließt einen Kreis", "Grad": f"verworfen: an {inst.name(u)} oder {inst.name(v)} wäre die Gradschranke überschritten"}[s.status]
    st.caption(f"Schritt {step}: Leitung {inst.label(s.edge)} (Kosten {kosten(c)}) – {why}. Grün-blau: gewählt, rot gestrichelt: verworfen, grau: noch nicht angesehen, Zahlen: Kosten. Das Depot A ist orange.")
else:
    st.caption("Noch keine Leitung angesehen. Grau: mögliche Leitungen, Zahlen: Kosten, das Depot A ist orange.")

m1, m2, m3 = st.columns(3)
# Delta immer als „mein Wert minus Referenz“; die Farbe regelt delta_color="inverse" (Vorzeichen-Falle, DEMO-PLAYBOOK §2).
if a.cost is not None and a.opt_cost is not None:
    if a.cost == a.opt_cost:
        m1.metric("Kosten des Greedy-Baums", kosten(a.cost), delta="so billig wie das Optimum", delta_color="off")
    else:
        m1.metric("Kosten des Greedy-Baums", kosten(a.cost), delta=f"{a.cost - a.opt_cost:+g} gegen das Optimum", delta_color="inverse")
else:
    m1.metric("Kosten des Greedy-Baums", "kein Spannbaum", delta=f"{len(a.tree)} von {inst.n - 1} Leitungen", delta_color="off")
m2.metric("Kosten des besten Spannbaums", kosten(a.opt_cost) if a.opt_cost is not None else "–", delta=f"{a.n_opt} optimal" if a.n_trees else None, delta_color="off")
m3.metric("Spannbäume mit der Nebenbedingung", a.n_trees, delta=grade_label(settings.grad), delta_color="off")

if st.button("📄 PDF des aktuellen Plans erstellen", key="pdf_make"):
    st.session_state["pdf_made"] = (settings, build_pdf(a, settings))
made = st.session_state.get("pdf_made")
if made and made[0] == settings:
    st.download_button("⬇️ PDF herunterladen", data=made[1], file_name="greedy-und-tausch.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Ist die Greedy-Regel hier optimal?")
kind, text = verdict_optimal(a, settings.grad)
getattr(st, kind)(text)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Kennt die Regel nur die Reihenfolge der Kosten?")
st.caption(
    "Alle Kosten streng wachsend umrechnen und prüfen, ob sich der Kruskal-Baum ändert. Zum Vergleich der Baum der billigsten Wege vom Depot "
    "(Dijkstra), der von den Kostenwerten abhängt. Anteile über 40 feste Pläne mit der Standortzahl und der Nabe aus der Seitenleiste."
)
name1 = st.selectbox("Umrechnung der Kosten", C.TRANSFORMS, key="e1_transform")
cur = transform_current(a, name1)
c1, c2 = st.columns(2)
c1.metric("Kruskal-Baum auf diesem Plan", "unverändert" if cur["kruskal_same"] else "geändert")
c2.metric("Baum der billigsten Wege auf diesem Plan", "unverändert" if cur["spt_same"] else "geändert")
rows1 = _transform_table(settings.n, settings.nabe)
st.dataframe(
    [{"Umrechnung": r["name"], "Pläne": r["instances"], "Kruskal-Baum geändert": r["kruskal_changed"], "Baum der billigsten Wege geändert": r["spt_changed"]} for r in rows1],
    hide_index=True, width="stretch",
)
kind, text = verdict_transform(rows1)
getattr(st, kind)(text)

st.subheader("🔬 Experiment 2: Ist Greedy für jede Größe gleichzeitig optimal?")
st.caption(
    f"Für jedes k: Kosten der ersten k von Greedy genommenen Leitungen gegen die kleinsten Kosten eines Waldes mit k Leitungen (alle Wälder aufgezählt, mit {grade_label(settings.grad)}). "
    "Die Nebenbedingung stammt aus der Seitenleiste."
)
rows2 = _prefix(settings)
st.plotly_chart(build_prefix_chart(rows2), width="stretch", key="prefix_chart")
kind, text = verdict_prefix(rows2, settings.grad)
getattr(st, kind)(text)

st.subheader("🔬 Experiment 3: Führt Tauschen immer zum Optimum?")
st.caption(f"Von einem zufälligen zulässigen Spannbaum aus so lange verbessernd tauschen, bis es keinen erlaubten Tausch mehr gibt ({grade_label(settings.grad)}).")
rule = st.selectbox("Welcher verbessernde Tausch?", ("zufällig", "bester"), key="e3_rule", help="'zufällig': unter allen verbessernden Tauschen gleichverteilt; 'bester': die größte Kostensenkung.")
if "e3_seed" not in st.session_state:
    st.session_state["e3_seed"] = C.DEFAULT_START
st.button("🎲 Neuen Startbaum ziehen", key="e3_new", on_click=lambda: st.session_state.update(e3_seed=st.session_state["e3_seed"] + 1))
run = _swap_run(settings, rule, st.session_state["e3_seed"])
if run is None:
    kind, text = verdict_swaps(None, settings.grad)
    getattr(st, kind)(text)
else:
    last = len(run["swaps"])
    if st.session_state.get("e3_step", 0) > last:
        st.session_state["e3_step"] = last
    if last:
        t_step = st.slider("Nach wie vielen Tauschen?", 0, last, 0, key="e3_step")
    else:
        t_step = 0
        st.caption("Der Startbaum ist schon ein lokales Optimum: kein erlaubter verbessernder Tausch.")
    tree = run["trees"][t_step]
    nxt = run["swaps"][t_step] if t_step < last else (None, None)
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(build_map(inst, taken=tree, swap_in=nxt[0], swap_out=nxt[1], height=460), width="stretch", key="swap_map")
    with col_b:
        st.plotly_chart(build_swap_chart(run), width="stretch", key="swap_chart")
    if nxt[0] is not None:
        st.caption(f"{nach_tausch(t_step)}: Kosten {kosten(run['costs'][t_step])}. Nächster Tausch: {inst.label(nxt[0])} kommt hinzu (grün gestrichelt), {inst.label(nxt[1])} entfällt (orange gestrichelt).")
    else:
        st.caption(f"{nach_tausch(t_step)}: Kosten {kosten(run['costs'][t_step])}. Kein erlaubter verbessernder Tausch mehr.")
    kind, text = verdict_swaps(run, settings.grad)
    getattr(st, kind)(text)

st.subheader("🔬 Experiment 4: Was kippt, wenn eine Gradschranke dazukommt?")
st.caption(
    "Dieselben drei Prüfungen über 40 feste Pläne (Standortzahl und Nabe aus der Seitenleiste), für alle Schranken. Je Plan drei Tausch-Läufe von zufälligen zulässigen Startbäumen. "
    "Pläne ohne zulässigen Spannbaum zählen nicht mit."
)
if st.button("📊 Auf 40 festen Plänen messen", key="e4_run"):
    st.session_state["e4_done"] = True
if st.session_state.get("e4_done"):
    rows4 = _grad_stats(settings.n, settings.nabe)
    st.dataframe(
        [
            {
                "Leitungen je Standort": _grade_name(r["grad"]), "Pläne": r["instances"], "ohne Spannbaum": r["no_tree"], "Schranke bindet": r["binds"],
                "Greedy nicht optimal": r["greedy_worse"], "Greedy ohne Spannbaum": r["greedy_none"], "Tausch hängt (Läufe)": f"{r['stuck']} von {r['runs']}",
            }
            for r in rows4
        ],
        hide_index=True, width="stretch",
    )
    kind, text = verdict_grad(rows4)
    getattr(st, kind)(text)

st.subheader("🔬 Experiment 5: Hat jeder Tausch einen Partner? (Ausblick auf das Matroid)")
st.caption(
    f"Aus der Menge der zulässigen Bäume Paare (T1, T2) ziehen. Für jede Leitung e in T1 ohne T2: gibt es eine Leitung f in T2 ohne T1, sodass T1 − e + f wieder zulässig ist? "
    f"Zusätzlich symmetrisch: auch T2 − f + e zulässig. {len(C.AXIOM_SEEDS)} feste Pläne mit {C.AXIOM_N} Standorten ohne Nabe, je {C.AXIOM_PAIRS} zufällige Baumpaare."
)
if st.button("📊 Tausch-Eigenschaft messen", key="e5_run"):
    st.session_state["e5_done"] = True
if st.session_state.get("e5_done"):
    rows5 = _axiom_stats()
    st.dataframe(
        [
            {
                "Familie": r["label"], "Tripel (T1, T2, e)": r["triples"],
                "ohne Austauschpartner": f"{r['fail']} ({de(100.0 * r['fail'] / r['triples'])} %)",
                "ohne symmetrischen Partner": f"{r['sym_fail']} ({de(100.0 * r['sym_fail'] / r['triples'])} %)",
            }
            for r in rows5
        ],
        hide_index=True, width="stretch",
    )
    kind, text = verdict_axiom(rows5)
    getattr(st, kind)(text)

st.markdown("---")

# --- Spielwiese ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🛠️ Spielwiese: selbst tauschen")
st.caption(f"Ein zufälliger zulässiger Spannbaum ({grade_label(settings.grad)}). Wählen Sie eine neue Leitung; der Kreis, den sie schließt, wird orange. Dann wählen Sie, welche Leitung des Kreises entfällt.")
play_key = (settings, st.session_state.get("play_seed", 0))
if st.session_state.get("play_key") != play_key:
    start = A.random_start(inst, settings.grad, st.session_state.get("play_seed", 0))
    st.session_state["play_tree"] = tuple(sorted(start)) if start else None
    st.session_state["play_key"] = play_key
    st.session_state["play_msg"] = None
    st.session_state.pop("play_in", None)
    st.session_state.pop("play_out", None)
play_tree = st.session_state.get("play_tree")


def _reroll():
    st.session_state["play_seed"] = st.session_state.get("play_seed", 0) + 1


def _do_swap():
    tree = st.session_state["play_tree"]
    e_in, f_out = st.session_state.get("play_in"), st.session_state.get("play_out")
    if e_in is None or f_out is None or not A.swap_ok(inst, tree, e_in, f_out, settings.grad):
        st.session_state["play_msg"] = ("warning", "Dieser Tausch ist nicht erlaubt: die Leitung muss auf dem Kreis liegen, und die Gradschranke gilt weiter.")
        return
    before = A.cost_of(inst, tree)
    st.session_state["play_tree"] = A.apply_swap(tree, e_in, f_out)
    after = A.cost_of(inst, st.session_state["play_tree"])
    st.session_state["play_msg"] = (
        "success" if after < before else "info",
        f"{inst.label(e_in)} hinein, {inst.label(f_out)} heraus: Kosten {kosten(before)} → {kosten(after)}.",
    )
    st.session_state.pop("play_in", None)
    st.session_state.pop("play_out", None)


if play_tree is None:
    st.info(f"Mit {grade_label(settings.grad)} gibt es auf diesem Plan keinen Spannbaum.")
else:
    outside = [e for e in range(inst.m) if e not in play_tree]
    e_in = None
    cyc = []
    play_left, play_right = st.columns(2)
    with play_right:
        if outside:
            e_in = st.selectbox("Neue Leitung", outside, key="play_in", format_func=lambda e: f"{inst.label(e)} (Kosten {kosten(inst.edges[e][2])})")
            cyc = A.cycle_edges(inst, play_tree, e_in)
            st.selectbox("Entfallende Leitung (auf dem Kreis)", cyc, key="play_out", format_func=lambda e: f"{inst.label(e)} (Kosten {kosten(inst.edges[e][2])})")
        cc1, cc2 = st.columns(2)
        cc1.button("🔄 Tausch ausführen", key="play_do", on_click=_do_swap, disabled=not outside, width="stretch")
        cc2.button("🎲 Neuer Zufallsbaum", key="play_new", on_click=_reroll, width="stretch")
        msg = st.session_state.get("play_msg")
        if msg:
            getattr(st, msg[0])(msg[1])
        status = play_status(inst, play_tree, settings.grad)
        better = ", ".join(f"{inst.label(e)} hinein / {inst.label(f)} heraus (−{kosten(inst.edges[f][2] - inst.edges[e][2])})" for e, f in status["swaps"][:6])
        st.caption(
            f"Kosten des Baums: {kosten(status['cost'])}; Optimum: {kosten(status['opt_cost'])}. "
            + (f"Verbessernde Tausche ({len(status['swaps'])}): {better}{' …' if len(status['swaps']) > 6 else ''}." if status["swaps"] else "Kein erlaubter verbessernder Tausch mehr.")
        )
    with play_left:
        st.plotly_chart(build_map(inst, taken=play_tree, cycle=cyc, swap_in=e_in, height=460), width="stretch", key="play_map")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Nebenbedingung ist „kein Kreis“** | Mit einer Gradschranke findet dieselbe Regel nicht immer den besten Baum und manchmal gar keinen Spannbaum (Experiment 4); die Tausch-Lokalsuche bleibt hängen. | Stück 2 (wo Greedy scheitert) und Stück 3 (das Matroid) |
| **Kleine Pläne (bis 9 Standorte, höchstens 16 mögliche Leitungen)** | Das Aufzählen aller Bäume ist hier die Prüfung. Für große Pläne ist „Greedy ist optimal“ ein Satz, den diese Demo nicht an großen Instanzen misst. | Stück 5 (Greedy genau dann optimal) |
| **Die drei Eigenschaften sind Beobachtungen** | Sie gelten auf allen gemessenen Plänen ohne Schranke (Eigenschaft 1 an 40 Plänen, 2 und 3 am gewählten Plan bzw. in 120 Läufen). Die Messung ersetzt keinen Beweis; die drei Sätze sind bekannt. | Stück 5 |
| **Ein Plantyp, eine Art Nebenbedingung** | Zufällige Standorte, Depot in der Mitte, Kosten aus Entfernungen; nur die Gradschranke. Andere Nebenbedingungen (Farben, Kapazitäten) kommen in späteren Stücken. | Stück 2, 7 |
| **Gleichstände** | Bei gleichen Kosten gibt es oft mehrere beste Bäume; Greedy findet einen davon. | `kruskal-demo` (Gleichstände) |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben** ein Graph $G = (V, E)$ mit Kosten $c_e$ und optional einer Gradschranke $d$. **Gesucht** ein Spannbaum $T \subseteq E$ (zusammenhängend, kreisfrei, $|T| = |V| - 1$), der $\sum_{e \in T} c_e$ minimiert, mit $\deg_T(v) \le d$ für alle $v$, falls eine Schranke gilt.

| Symbol | Bedeutung |
|---|---|
| $V$, $E$ | Standorte und mögliche Leitungen |
| $c_e$ | Kosten der Leitung $e$ (ganze Zahl) |
| $T$ | Spannbaum, $\lvert T \rvert = \lvert V \rvert - 1$ |
| $d$ | Höchstzahl der Leitungen je Standort |

**Greedy.** Ordne $E$ nach $(c_e, e)$. Nimm $e$, wenn $T \cup \{e\}$ kreisfrei bleibt (und mit Schranke $d$ kein Standort über $d$ käme).

**Tausch.** Für $T$ und $e \notin T$ enthält $T \cup \{e\}$ genau einen Kreis $C(T, e)$. Für $f \in C(T, e)$ ist $T - f + e$ wieder ein Spannbaum; er ist billiger, wenn $c_f > c_e$.

**Die drei Eigenschaften** (als Sätze bekannt, hier an den Plänen ohne Schranke nachgemessen, siehe die Experimente): (1) der Greedy-Baum hängt nur von der Ordnung der $c_e$ ab; (2) für jedes $k$ sind die ersten $k$ gewählten Kanten ein billigster Wald mit $k$ Kanten; (3) jeder Spannbaum ohne verbessernden Tausch ist optimal.

**Literatur.** Kruskal, J. B. (1956): *On the shortest spanning subtree of a graph and the traveling salesman problem*, Proc. Amer. Math. Soc. 7(1), 48–50. Edmonds, J. (1971): *Matroids and the greedy algorithm*, Mathematical Programming 1, 127–136.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Matroide: vom Spannbaum zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-matroide.html)."
)
