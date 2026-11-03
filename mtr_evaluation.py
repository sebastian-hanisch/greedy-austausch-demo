"""Kennzahlen, Verdikt-Logik und Messreihen über feste Instanzen. Alle sichtbaren Zahlen kommen aus diesen Funktionen."""

import random
from dataclasses import dataclass

import mtr_algorithm as A
import mtr_constants as C
from mtr_scenario import Instance, make_instance


def de(x: float, digits: int = 1) -> str:
    """Zahl mit Dezimalkomma."""
    return f"{x:.{digits}f}".replace(".", ",")


def kosten(x: float) -> str:
    """Kosten als ganze Zahl, wenn sie ganz sind, sonst mit einer Stelle."""
    return str(int(x)) if float(x).is_integer() else de(x, 1)


def grade_label(grad: int) -> str:
    return "keine Gradschranke" if grad == C.GRADE_OFF else f"höchstens {grad} Leitungen je Standort"


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    seed: int = C.DEFAULT_SEED
    nabe: bool = False
    grad: int = C.GRADE_OFF


@dataclass(frozen=True)
class Analysis:
    inst: Instance
    steps: tuple          # Greedy mit der gewählten Schranke, ein Schritt je Kante
    free_steps: tuple     # Kruskal ohne Schranke
    tree: tuple           # die von Greedy genommenen Kanten
    is_tree: bool         # hat Greedy einen Spannbaum gefunden?
    cost: float | None    # Kosten des Greedy-Baums, nur wenn er ein Spannbaum ist
    free_cost: float      # Kosten des freien Kruskal-Baums
    binds: bool           # verletzt der freie Kruskal-Baum die Schranke?
    n_trees: int          # Spannbäume, die die Schranke einhalten
    opt_cost: float | None
    n_opt: int


def analyse(settings: Settings) -> Analysis:
    inst = make_instance(settings.n, settings.seed, settings.nabe)
    steps = tuple(A.greedy_steps(inst, settings.grad))
    free_steps = tuple(A.greedy_steps(inst, C.GRADE_OFF))
    tree = A.taken(steps)
    free = A.taken(free_steps)
    is_tree = len(tree) == inst.n - 1
    best, opts = A.optimum_trees(inst, settings.grad)
    trees = A.all_trees(inst, settings.grad)
    binds = bool(settings.grad) and max(A.degrees(inst, free), default=0) > settings.grad
    return Analysis(
        inst, steps, free_steps, tree, is_tree, A.cost_of(inst, tree) if is_tree else None, A.cost_of(inst, free), binds, len(trees), best, len(opts)
    )


def percent_over(value: float, reference: float) -> float:
    """Wie viel Prozent der Referenz `value` darüber liegt; ohne Referenzkosten gibt es keinen Anteil."""
    return 0.0 if reference <= 0 else 100.0 * (value - reference) / reference


def verdict_optimal(a: Analysis, grad: int) -> tuple[str, str]:
    """Verdikt der Kernfrage: Ist die Greedy-Regel hier optimal?"""
    if a.n_trees == 0:
        return "info", f"Mit {grade_label(grad)} gibt es auf diesem Plan keinen Spannbaum: kein Netz verbindet alle Standorte."
    if not a.is_tree:
        return "warning", (
            f"Greedy bleibt nach {len(a.tree)} von {a.inst.n - 1} nötigen Leitungen stehen und findet **keinen** Spannbaum, "
            f"obwohl es {'einen Spannbaum' if a.n_trees == 1 else f'{a.n_trees} Spannbäume'} gibt (der billigste kostet {kosten(a.opt_cost)})."
        )
    if a.cost == a.opt_cost:
        if grad and a.binds:
            return "info", (
                f"Die Schranke bindet (der freie Baum hätte zu viele Leitungen an einem Standort), und Greedy trifft trotzdem das Optimum "
                f"({kosten(a.cost)}). Das ist ein Zufall dieses Plans, kein Gesetz."
            )
        extra = " Die Schranke bindet hier nicht." if grad else ""
        if a.n_trees == 1:
            found = "Es gibt auf diesem Plan nur einen Spannbaum, und Greedy findet ihn."
        elif a.n_opt == 1:
            found = f"Unter {a.n_trees} Spannbäumen ist genau einer optimal, und Greedy findet ihn."
        else:
            found = f"Unter {a.n_trees} Spannbäumen sind {a.n_opt} optimal, Greedy findet einen davon."
        return "success", f"Greedy trifft das Optimum: Kosten {kosten(a.cost)}. {found}{extra}"
    return "warning", (
        f"Greedy liefert Kosten {kosten(a.cost)}, das Optimum ist {kosten(a.opt_cost)}: der Greedy-Baum liegt "
        f"**{de(percent_over(a.cost, a.opt_cost))} %** über dem besten (von {a.n_trees} Spannbäumen)."
    )


# --- Fingerabdruck 1: nur die Reihenfolge -----------------------------------------------------------------------------------------------


def transform_current(a: Analysis, name: str) -> dict:
    """Auf dem aktuellen Plan: bleibt der Kruskal-Baum bei der Umrechnung gleich, und der Baum der billigsten Wege vom Depot?"""
    t = A.transformed(a.inst, name)
    return {
        "name": name,
        "kruskal_same": frozenset(A.taken(A.greedy_steps(t))) == frozenset(A.taken(a.free_steps)),
        "spt_same": A.shortest_path_tree(t) == A.shortest_path_tree(a.inst),
    }


def transform_table(n: int, nabe: bool, seeds=C.SWEEP_SEEDS) -> list[dict]:
    """Für jede Umrechnung: in wie vielen der festen Instanzen ändert sich der Kruskal-Baum, in wie vielen der Baum der billigsten Wege?"""
    rows = []
    insts = [make_instance(n, s, nabe) for s in seeds]
    base_k = [frozenset(A.taken(A.greedy_steps(i))) for i in insts]
    base_s = [A.shortest_path_tree(i) for i in insts]
    for name in C.TRANSFORMS:
        k_changed = s_changed = 0
        for i, bk, bs in zip(insts, base_k, base_s):
            t = A.transformed(i, name)
            k_changed += frozenset(A.taken(A.greedy_steps(t))) != bk
            s_changed += A.shortest_path_tree(t) != bs
        rows.append({"name": name, "instances": len(insts), "kruskal_changed": k_changed, "spt_changed": s_changed})
    return rows


def verdict_transform(rows: list[dict]) -> tuple[str, str]:
    k = sum(r["kruskal_changed"] for r in rows)
    total = sum(r["instances"] for r in rows)
    s_min = min(r["spt_changed"] for r in rows)
    s_max = max(r["spt_changed"] for r in rows)
    inst = rows[0]["instances"]
    if k == 0:
        return "success", (
            f"Der Kruskal-Baum ändert sich bei **keiner** der {len(rows)} Umrechnungen auf {inst} festen Plänen ({total} Vergleiche). "
            f"Der Baum der billigsten Wege vom Depot ändert sich je nach Umrechnung in {s_min} bis {s_max} von {inst} Plänen."
        )
    return "warning", f"Der Kruskal-Baum ändert sich in {k} von {total} Vergleichen. Das widerspricht der Erwartung, nur die Reihenfolge zähle."


# --- Fingerabdruck 2: jede Größe k gleichzeitig -----------------------------------------------------------------------------------------


def prefix_rows(a: Analysis, grad: int) -> list[dict]:
    """Für k = 1 .. n − 1: Kosten der ersten k Kanten von Greedy und kleinste Kosten eines Waldes mit k Kanten (mit derselben Schranke)."""
    best = A.best_forest_costs(a.inst, grad)
    pref = A.prefix_costs(a.inst, a.steps)
    rows = []
    for k in range(1, a.inst.n):
        g = pref[k - 1] if k <= len(pref) else None
        o = best.get(k)
        rows.append({"k": k, "greedy": g, "best": o, "equal": g is not None and o is not None and g == o})
    return rows


def verdict_prefix(rows: list[dict], grad: int) -> tuple[str, str]:
    if not rows:
        return "info", "Mit einem einzigen Standort gibt es keine Leitung und damit keine Größe k zu prüfen."
    bad = [r for r in rows if not r["equal"]]
    if not bad:
        return "success", f"Für **alle** {len(rows)} Größen k sind die ersten k Kanten von Greedy der billigste Wald mit k Kanten ({grade_label(grad)})."
    first = bad[0]
    ks = ", ".join(str(r["k"]) for r in bad)
    if first["greedy"] is None:
        what = "Greedy hat zu diesem k keine Kanten mehr genommen"
    else:
        what = f"Greedy hat {kosten(first['greedy'])}, der beste Wald {kosten(first['best'])}"
    return "warning", f"Bei {len(bad)} von {len(rows)} Größen (k = {ks}) ist Greedy nicht optimal. Erstes Versagen bei k = {first['k']}: {what}."


# --- Fingerabdruck 3: Tausch-Lokalsuche -------------------------------------------------------------------------------------------------


def swap_run(a: Analysis, grad: int, rule: str, seed: int):
    """Eine Tausch-Lokalsuche von einem zufälligen zulässigen Spannbaum. None, wenn es keinen Spannbaum gibt."""
    start = A.random_start(a.inst, grad, seed)
    if start is None:
        return None
    swaps = A.local_search(a.inst, start, grad, rule, seed)
    trees = [tuple(sorted(start))]
    for e, f in swaps:
        trees.append(A.apply_swap(trees[-1], e, f))
    best, opts = A.optimum_trees(a.inst, grad)
    end_cost = A.cost_of(a.inst, trees[-1])
    distance = min(len(set(start) - set(o)) for o in opts)
    return {
        "swaps": swaps, "trees": trees, "costs": [A.cost_of(a.inst, t) for t in trees], "opt_cost": best, "end_cost": end_cost,
        "distance": distance, "stuck": end_cost > best,
    }


def nach_tausch(n: int) -> str:
    return "Am Start" if n == 0 else ("Nach 1 Tausch" if n == 1 else f"Nach {n} Tauschen")


def verdict_swaps(run: dict | None, grad: int) -> tuple[str, str]:
    if run is None:
        return "info", f"Mit {grade_label(grad)} gibt es keinen Spannbaum, von dem aus getauscht werden könnte."
    steps = len(run["swaps"])
    if not run["stuck"]:
        lead = "Schon der Startbaum erlaubt keinen verbessernden Tausch" if steps == 0 else f"{nach_tausch(steps)} ist kein verbessernder Tausch mehr möglich"
        d = run["distance"]
        away = "Der Startbaum war schon optimal." if d == 0 else f"Der Startbaum war {'eine Kante' if d == 1 else f'{d} Kanten'} vom nächsten optimalen Baum entfernt."
        return "success", f"{lead}, und die Kosten ({kosten(run['end_cost'])}) sind das Optimum. {away}"
    return "warning", (
        f"{nach_tausch(steps)} gibt es keinen erlaubten verbessernden Tausch mehr, aber die Kosten {kosten(run['end_cost'])} liegen über dem Optimum "
        f"{kosten(run['opt_cost'])}: ein lokales Optimum, das nicht das beste ist."
    )


# --- Die Gradschranke kippt alles: Anteile über feste Instanzen -------------------------------------------------------------------------


def grad_statistics(n: int, nabe: bool, seeds=C.SWEEP_SEEDS, starts: int = C.LOCAL_STARTS) -> list[dict]:
    """Für jede Schranke (aus, 3, 2) über die festen Instanzen: bindet sie, ist Greedy nicht optimal, findet Greedy keinen Baum, bleibt die
    Tausch-Lokalsuche vor dem Optimum hängen (`starts` Läufe je Instanz). Instanzen ohne zulässigen Spannbaum zählen nicht mit."""
    rows = []
    insts = [make_instance(n, s, nabe) for s in seeds]
    for grad in C.GRADE_CHOICES:
        row = {"grad": grad, "instances": 0, "no_tree": 0, "binds": 0, "greedy_worse": 0, "greedy_none": 0, "runs": 0, "stuck": 0}
        for inst in insts:
            trees = A.all_trees(inst, grad)
            if not trees:
                row["no_tree"] += 1
                continue
            row["instances"] += 1
            best = min(A.cost_of(inst, t) for t in trees)
            taken = A.taken(A.greedy_steps(inst, grad))
            free = A.taken(A.greedy_steps(inst, C.GRADE_OFF))
            row["binds"] += bool(grad) and max(A.degrees(inst, free), default=0) > grad
            if len(taken) < inst.n - 1:
                row["greedy_none"] += 1
            elif A.cost_of(inst, taken) > best:
                row["greedy_worse"] += 1
            for s in range(starts):
                start = random.Random(s).choice(trees)
                end = A.apply_swaps(start, A.local_search(inst, start, grad, "zufällig", s))
                row["runs"] += 1
                row["stuck"] += A.cost_of(inst, end) > best
        rows.append(row)
    return rows


def verdict_grad(rows: list[dict]) -> tuple[str, str]:
    free = rows[0]
    if free["greedy_worse"] or free["greedy_none"] or free["stuck"]:
        return "warning", "Ohne Schranke ist Greedy oder die Tausch-Lokalsuche in dieser Messung nicht immer optimal. Das widerspricht der Erwartung."
    parts = []
    for r in rows[1:]:
        parts.append(
            f"**{grade_label(r['grad'])}**: die Schranke bindet in {r['binds']} von {r['instances']} Plänen, Greedy ist in {r['greedy_worse']} nicht optimal "
            f"und findet in {r['greedy_none']} keinen Spannbaum, die Tausch-Lokalsuche bleibt in {r['stuck']} von {r['runs']} Läufen vor dem Optimum hängen"
        )
    return "info", f"Ohne Schranke: 0 Abweichungen bei {free['instances']} Plänen und {free['runs']} Läufen. " + "; ".join(parts) + "."


# --- Ausblick Stück 3: die Tausch-Eigenschaft -------------------------------------------------------------------------------------------


def axiom_statistics(seeds=C.AXIOM_SEEDS, pairs: int = C.AXIOM_PAIRS, n: int = C.AXIOM_N) -> list[dict]:
    rows = []
    for label, grad in (("Spannbäume", C.GRADE_OFF), ("Spannbäume mit höchstens 3 Leitungen je Standort", 3), ("Pfade (höchstens 2 Leitungen je Standort)", 2)):
        triples = fail = sym_fail = 0
        for s in seeds:
            inst = make_instance(n, s, False)
            family = A.all_trees(inst, grad)
            t, f, sf = A.exchange_counts(inst, family, pairs, s)
            triples += t
            fail += f
            sym_fail += sf
        rows.append({"label": label, "triples": triples, "fail": fail, "sym_fail": sym_fail})
    return rows


def verdict_axiom(rows: list[dict]) -> tuple[str, str]:
    base = rows[0]
    if base["fail"] or base["sym_fail"]:
        return "warning", "Bei den Spannbäumen gibt es Tripel ohne Austauschpartner. Das widerspricht der Erwartung."
    parts = [f"{r['label']}: {de(100.0 * r['fail'] / r['triples'])} % ohne Austauschpartner, {de(100.0 * r['sym_fail'] / r['triples'])} % ohne symmetrischen" for r in rows[1:]]
    return "info", f"Bei den Spannbäumen findet jedes der {base['triples']} Tripel einen Austauschpartner. " + "; ".join(parts) + "."


# --- Spielwiese -------------------------------------------------------------------------------------------------------------------------


def play_status(inst: Instance, tree, grad: int) -> dict:
    """Kosten, Verbesserungsmöglichkeiten und Optimum für den Baum, an dem man von Hand tauscht."""
    best, _ = A.optimum_trees(inst, grad)
    swaps = A.improving_swaps(inst, tree, grad)
    return {"cost": A.cost_of(inst, tree), "opt_cost": best, "swaps": swaps, "valid": A.check_tree(inst, tree, grad)}


def edge_table(a: Analysis) -> list[dict]:
    """Eine Zeile je Kante in Greedy-Reihenfolge: Kante, Kosten, Schritt, Entscheidung."""
    rows = []
    for i, s in enumerate(a.steps, start=1):
        u, v, c = a.inst.edges[s.edge]
        text = {"genommen": "genommen", "Kreis": "Kreis", "Grad": "Gradschranke"}[s.status]
        rows.append({"Schritt": i, "Leitung": a.inst.label(s.edge), "Kosten": kosten(c), "Entscheidung": text})
    return rows
