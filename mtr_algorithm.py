"""Kern der Demo (nur Standardbibliothek): Greedy (Kruskal) mit und ohne Gradschranke, Aufzählen, Tausch-Lokalsuche, Tausch-Eigenschaft.

Jede Regel ist eine eigene Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK §1b). Kanten werden über ihren Index in
`Instance.edges` angesprochen. `maxdeg == 0` heißt: keine Gradschranke (siehe C.GRADE_OFF)."""

import heapq
import itertools
import math
import random
from dataclasses import dataclass

from mtr_scenario import Instance, with_costs


# --- Prüfer (unabhängig vom Greedy: Tiefensuche statt Union-Find) -----------------------------------------------------------------------


def degrees(inst: Instance, edge_ids) -> list[int]:
    d = [0] * inst.n
    for e in edge_ids:
        u, v, _ = inst.edges[e]
        d[u] += 1
        d[v] += 1
    return d


def components(inst: Instance, edge_ids) -> int:
    """Zahl der Zusammenhangskomponenten des Graphen (alle Standorte, nur die gegebenen Leitungen), per Tiefensuche."""
    adj = {v: [] for v in range(inst.n)}
    for e in edge_ids:
        u, v, _ = inst.edges[e]
        adj[u].append(v)
        adj[v].append(u)
    seen, count = set(), 0
    for s in range(inst.n):
        if s in seen:
            continue
        count += 1
        stack = [s]
        while stack:
            x = stack.pop()
            if x not in seen:
                seen.add(x)
                stack.extend(adj[x])
    return count


def check_forest(inst: Instance, edge_ids, maxdeg: int = 0) -> bool:
    """Wald: verschiedene Kanten, kein Kreis (Zahl der Komponenten = Standorte − Kanten), Grad höchstens maxdeg."""
    edge_ids = tuple(edge_ids)
    if len(set(edge_ids)) != len(edge_ids) or any(not 0 <= e < inst.m for e in edge_ids):
        return False
    if components(inst, edge_ids) != inst.n - len(edge_ids):
        return False
    return maxdeg == 0 or max(degrees(inst, edge_ids), default=0) <= maxdeg


def check_tree(inst: Instance, edge_ids, maxdeg: int = 0) -> bool:
    """Spannbaum: ein Wald mit Standorte − 1 Kanten."""
    edge_ids = tuple(edge_ids)
    return len(edge_ids) == inst.n - 1 and check_forest(inst, edge_ids, maxdeg)


def cost_of(inst: Instance, edge_ids) -> float:
    return sum(inst.edges[e][2] for e in edge_ids)


# --- Greedy ---------------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Step:
    edge: int
    status: str  # "genommen", "Kreis" (schließt einen Kreis) oder "Grad" (ein Standort hätte zu viele Leitungen)


def edge_order(inst: Instance) -> list[int]:
    """Reihenfolge der Kanten nach (Kosten, Index): bei gleichen Kosten gewinnt der kleinere Index."""
    return sorted(range(inst.m), key=lambda e: (inst.edges[e][2], e))


def greedy_steps(inst: Instance, maxdeg: int = 0) -> list[Step]:
    """Kruskal mit optionaler Gradschranke: Kanten in Kostenreihenfolge, genommen, wenn sie keinen Kreis schließen und
    kein Standort über maxdeg käme. Liefert für jede Kante einen Schritt (auch nach dem letzten Baumschritt)."""
    parent = list(range(inst.n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    deg = [0] * inst.n
    steps = []
    for e in edge_order(inst):
        u, v, _ = inst.edges[e]
        if maxdeg and (deg[u] >= maxdeg or deg[v] >= maxdeg):
            steps.append(Step(e, "Grad"))
            continue
        a, b = find(u), find(v)
        if a == b:
            steps.append(Step(e, "Kreis"))
            continue
        parent[a] = b
        deg[u] += 1
        deg[v] += 1
        steps.append(Step(e, "genommen"))
    return steps


def taken(steps) -> tuple[int, ...]:
    """Die genommenen Kanten in der Reihenfolge, in der Greedy sie nahm."""
    return tuple(s.edge for s in steps if s.status == "genommen")


# --- Aufzählen ------------------------------------------------------------------------------------------------------------------------


def enumerate_forests(inst: Instance, maxdeg: int = 0):
    """Alle Wälder (auch den leeren) als aufsteigende Kantentupel, mit Grad höchstens maxdeg. Rekursion über die Kanten in Indexreihenfolge."""
    edges = inst.edges

    def rec(i, comp, deg, chosen):
        yield tuple(chosen)
        for j in range(i, len(edges)):
            u, v, _ = edges[j]
            if comp[u] == comp[v] or (maxdeg and (deg[u] >= maxdeg or deg[v] >= maxdeg)):
                continue
            cu, cv = comp[u], comp[v]
            merged = [cu if c == cv else c for c in comp]
            deg[u] += 1
            deg[v] += 1
            chosen.append(j)
            yield from rec(j + 1, merged, deg, chosen)
            chosen.pop()
            deg[u] -= 1
            deg[v] -= 1

    yield from rec(0, list(range(inst.n)), [0] * inst.n, [])


def all_trees(inst: Instance, maxdeg: int = 0) -> list[tuple[int, ...]]:
    """Alle Spannbäume mit Grad höchstens maxdeg (leere Liste, wenn es keinen gibt)."""
    return [f for f in enumerate_forests(inst, maxdeg) if len(f) == inst.n - 1]


def best_forest_costs(inst: Instance, maxdeg: int = 0) -> dict[int, float]:
    """Kleinste Kosten eines Waldes mit k Kanten, für jedes k, das es gibt."""
    best: dict[int, float] = {}
    for f in enumerate_forests(inst, maxdeg):
        c = cost_of(inst, f)
        if len(f) not in best or c < best[len(f)]:
            best[len(f)] = c
    return best


def optimum_trees(inst: Instance, maxdeg: int = 0):
    """(kleinste Kosten, Liste der optimalen Spannbäume) oder (None, []) ohne Spannbaum."""
    trees = all_trees(inst, maxdeg)
    if not trees:
        return None, []
    best = min(cost_of(inst, t) for t in trees)
    return best, [t for t in trees if cost_of(inst, t) == best]


# --- Tausch ---------------------------------------------------------------------------------------------------------------------------


def tree_path(inst: Instance, tree, a: int, b: int) -> list[int]:
    """Kanten des einzigen Weges von a nach b im Baum (leer bei a == b)."""
    adj = {v: [] for v in range(inst.n)}
    for e in tree:
        u, v, _ = inst.edges[e]
        adj[u].append((v, e))
        adj[v].append((u, e))
    stack = [(a, -1, [])]
    while stack:
        x, parent, path = stack.pop()
        if x == b:
            return path
        for y, e in adj[x]:
            if y != parent:
                stack.append((y, x, path + [e]))
    raise ValueError("kein Weg: die Kanten bilden keinen zusammenhängenden Baum")


def cycle_edges(inst: Instance, tree, e_in: int) -> list[int]:
    """Die Baumkanten, die zusammen mit der neuen Kante e_in einen Kreis bilden."""
    u, v, _ = inst.edges[e_in]
    return tree_path(inst, tree, u, v)


def swap_ok(inst: Instance, tree, e_in: int, f_out: int, maxdeg: int = 0) -> bool:
    """Ist der Tausch (e_in hinein, f_out heraus) erlaubt: f_out liegt auf dem Kreis von e_in, und der Grad bleibt in der Schranke?"""
    if e_in in tree or f_out not in cycle_edges(inst, tree, e_in):
        return False
    return not maxdeg or max(degrees(inst, apply_swap(tree, e_in, f_out)), default=0) <= maxdeg


def apply_swap(tree, e_in: int, f_out: int) -> tuple[int, ...]:
    return tuple(sorted((set(tree) - {f_out}) | {e_in}))


def improving_swaps(inst: Instance, tree, maxdeg: int = 0) -> list[tuple[int, int]]:
    """Alle erlaubten Tausche, die strikt billiger machen: neue Kante hinein, eine teurere Kante ihres Kreises heraus."""
    out = []
    for e in range(inst.m):
        if e in tree:
            continue
        for f in cycle_edges(inst, tree, e):
            if inst.edges[f][2] > inst.edges[e][2] and swap_ok(inst, tree, e, f, maxdeg):
                out.append((e, f))
    return out


def local_search(inst: Instance, start, maxdeg: int = 0, rule: str = "zufällig", seed: int = 0) -> list[tuple[int, int]]:
    """Tausch-Lokalsuche: solange ein verbessernder Tausch existiert, einen ausführen. rule: "zufällig" (gleichverteilt unter den
    verbessernden) oder "bester" (größte Kostensenkung, bei Gleichstand die kleinsten Indizes). Liefert die Tauschfolge."""
    rng = random.Random(seed)
    tree = tuple(sorted(start))
    swaps = []
    while True:
        cand = improving_swaps(inst, tree, maxdeg)
        if not cand:
            return swaps
        if rule == "bester":
            e, f = min(cand, key=lambda ef: (inst.edges[ef[0]][2] - inst.edges[ef[1]][2], ef))
        else:
            e, f = rng.choice(cand)
        tree = apply_swap(tree, e, f)
        swaps.append((e, f))


def apply_swaps(start, swaps) -> tuple[int, ...]:
    tree = tuple(sorted(start))
    for e, f in swaps:
        tree = apply_swap(tree, e, f)
    return tree


def random_start(inst: Instance, maxdeg: int, seed: int):
    """Zufälliger zulässiger Spannbaum (gleichverteilt unter allen), oder None, wenn es keinen gibt."""
    trees = all_trees(inst, maxdeg)
    return random.Random(seed).choice(trees) if trees else None


# --- Fingerabdruck 1: nur die Reihenfolge ---------------------------------------------------------------------------------------------


def transform(name: str, c: float) -> float:
    """Streng wachsende Umrechnung eines Kostenwerts c >= 1."""
    if name == "hoch 3":
        return float(c) ** 3
    if name == "Logarithmus":
        return math.log(c) + 10.0
    if name == "plus 1000":
        return float(c) + 1000.0
    if name == "Exponentialfunktion":
        return math.exp(c / 50.0)
    if name == "Wurzel":
        return math.sqrt(c)
    raise ValueError(f"unbekannte Umrechnung: {name}")


def transformed(inst: Instance, name: str) -> Instance:
    return with_costs(inst, [transform(name, c) for (_, _, c) in inst.edges])


def shortest_path_tree(inst: Instance, root: int = 0) -> frozenset:
    """Baum der billigsten Wege von root (Dijkstra, bei Gleichstand der kleinere Knoten): die Kanten, über die jeder Standort erreicht wird."""
    adj = {v: [] for v in range(inst.n)}
    for e, (u, v, c) in enumerate(inst.edges):
        adj[u].append((v, e, c))
        adj[v].append((u, e, c))
    dist = {root: 0.0}
    via = {}
    heap = [(0.0, root)]
    done = set()
    while heap:
        d, x = heapq.heappop(heap)
        if x in done:
            continue
        done.add(x)
        for y, e, c in adj[x]:
            nd = d + c
            if y not in done and (y not in dist or nd < dist[y] - 1e-12):
                dist[y] = nd
                via[y] = e
                heapq.heappush(heap, (nd, y))
    return frozenset(via.values())


# --- Tausch-Eigenschaft (Ausblick auf das Matroid) -----------------------------------------------------------------------------------


def exchange_counts(inst: Instance, family, pairs: int, seed: int):
    """Stichprobe von Baumpaaren (T1, T2) aus `family` (Liste von Kantentupeln). Für jede Kante e in T1 ohne T2: gibt es f in T2 ohne T1,
    sodass T1 − e + f wieder in der Familie liegt (einseitig), und sodass zusätzlich T2 − f + e in der Familie liegt (symmetrisch)?
    Liefert (Zahl der Tripel, ohne einseitigen Partner, ohne symmetrischen Partner)."""
    members = {tuple(sorted(t)) for t in family}
    if len(family) < 2:
        return 0, 0, 0
    rng = random.Random(seed)
    triples = fail = sym_fail = 0
    for _ in range(pairs):
        t1, t2 = rng.sample(list(family), 2)
        s1, s2 = set(t1), set(t2)
        for e in sorted(s1 - s2):
            triples += 1
            one = any(tuple(sorted((s1 - {e}) | {f})) in members for f in s2 - s1)
            both = any(tuple(sorted((s1 - {e}) | {f})) in members and tuple(sorted((s2 - {f}) | {e})) in members for f in s2 - s1)
            fail += not one
            sym_fail += not both
    return triples, fail, sym_fail


def prefix_costs(inst: Instance, steps) -> list[float]:
    """Kosten der ersten k genommenen Kanten, k = 1, 2, ... (kumulativ)."""
    out, total = [], 0.0
    for e in taken(steps):
        total += inst.edges[e][2]
        out.append(total)
    return out


def count_forests_by_size(inst: Instance, maxdeg: int = 0) -> dict[int, int]:
    return {k: sum(1 for _ in g) for k, g in itertools.groupby(sorted(len(f) for f in enumerate_forests(inst, maxdeg)))}
