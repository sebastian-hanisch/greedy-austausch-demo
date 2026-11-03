"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import mtr_constants as C
from mtr_evaluation import kosten


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _lines(inst, edge_ids):
    xs, ys = [], []
    for e in edge_ids:
        u, v, _ = inst.edges[e]
        xs += [inst.points[u][0], inst.points[v][0], None]
        ys += [inst.points[u][1], inst.points[v][1], None]
    return xs, ys


def build_map(inst, taken=(), rejected=(), swap_in=None, swap_out=None, cycle=(), show_costs=True, height=430):
    """Plan der Standorte. Grau: mögliche Leitungen, dick grün-blau: gewählte Leitungen, rot gestrichelt: verworfen,
    orange: Kreis einer neuen Leitung, grün gestrichelt: neue Leitung eines Tauschs, orange gestrichelt: entfallende Leitung.
    Kostenbeschriftungen als Annotationen mit hellem Hintergrund (keine Text-Spur)."""
    special = set(taken) | set(rejected) | set(cycle) | ({swap_in} if swap_in is not None else set()) | ({swap_out} if swap_out is not None else set())
    other = [e for e in range(inst.m) if e not in special]
    fig = go.Figure()
    groups = [
        ("mögliche Leitung", other, dict(color=C.COLOR_OTHER, width=1.5), "solid"),
        ("Kreis der neuen Leitung", list(cycle), dict(color="rgba(240,163,10,0.9)", width=6), "solid"),
        ("gewählt", [e for e in taken if e not in cycle], dict(color=C.COLOR_TAKEN, width=5), "solid"),
        ("verworfen", list(rejected), dict(color=C.COLOR_REJECTED, width=2), "dash"),
    ]
    if swap_in is not None:
        groups.append(("kommt hinzu", [swap_in], dict(color=C.COLOR_IN, width=5), "dash"))
    if swap_out is not None:
        groups.append(("entfällt", [swap_out], dict(color=C.COLOR_OUT, width=5), "dash"))
    for name, ids, line, dash in groups:
        if not ids:
            continue
        xs, ys = _lines(inst, ids)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(dash=dash, **line), name=name, hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=[p[0] for p in inst.points], y=[p[1] for p in inst.points], mode="markers+text", text=[inst.name(v) for v in range(inst.n)],
        textposition="top center", textfont=dict(size=14),
        marker=dict(size=16, color=[C.COLOR_DEPOT] + [C.COLOR_NODE] * (inst.n - 1), line=dict(color="white", width=1.5)), name="Standort",
        hovertemplate="%{text}<extra></extra>", showlegend=False,
    ))
    fig.add_trace(go.Scatter(x=[-0.05, 1.05], y=[-0.05, 1.05], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    if show_costs:
        for e, (u, v, c) in enumerate(inst.edges):
            fig.add_annotation(
                x=(inst.points[u][0] + inst.points[v][0]) / 2, y=(inst.points[u][1] + inst.points[v][1]) / 2, text=kosten(c), showarrow=False,
                bgcolor="rgba(255,255,255,0.88)", font=dict(size=11, color="#222"), borderpad=1,
            )
    fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False)
    return _base(fig, height)


def build_prefix_chart(rows):
    """Kosten der ersten k Kanten von Greedy gegen die kleinsten Kosten eines Waldes mit k Kanten."""
    ks = [r["k"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ks, y=[r["best"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_LINE, width=3), name="bester Wald mit k Kanten",
                             hovertemplate="k = %{x}: %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=ks, y=[r["greedy"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_LINE2, width=2, dash="dot"),
                             marker=dict(size=9, symbol="diamond-open"), name="erste k Kanten von Greedy", hovertemplate="k = %{x}: %{y}<extra></extra>"))
    fig.update_xaxes(title_text="Kanten k", dtick=1)
    fig.update_yaxes(title_text="Kosten")
    return _base(fig)


def build_swap_chart(run):
    """Kosten des Baums nach jedem Tausch; waagerecht das Optimum."""
    steps = list(range(len(run["costs"])))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=steps, y=run["costs"], mode="lines+markers", line=dict(color=C.COLOR_LINE, width=3), name="Kosten des Baums",
                             hovertemplate="nach %{x} Tauschen: %{y}<extra></extra>"))
    fig.add_hline(y=run["opt_cost"], line=dict(color=C.COLOR_TAKEN, dash="dash"), annotation_text="Optimum", annotation_position="top right")
    fig.update_xaxes(title_text="Tausche", dtick=1)
    fig.update_yaxes(title_text="Kosten")
    return _base(fig, 300)
