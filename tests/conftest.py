"""Gemeinsame Fixtures: Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mtr_scenario import Instance  # noqa: E402

POINTS5 = ((0.5, 0.5), (0.2, 0.8), (0.8, 0.8), (0.2, 0.2), (0.8, 0.2))


@pytest.fixture
def mini():
    """5 Standorte, 7 Leitungen (Index: Leitung, Kosten): 0: A-B 4, 1: A-C 1, 2: B-C 2, 3: B-D 5, 4: C-D 8, 5: C-E 10, 6: D-E 3.
    Handrechnung: Kruskal nimmt 1, 2, 6, verwirft 0 (Kreis A-B-C) und nimmt 3: Kosten 1 + 2 + 3 + 5 = 11. Es gibt 21 Spannbäume."""
    return Instance(POINTS5, ((0, 1, 4), (0, 2, 1), (1, 2, 2), (1, 3, 5), (2, 3, 8), (2, 4, 10), (3, 4, 3)))


@pytest.fixture
def engpass():
    """Nabe A mit drei billigen Leitungen (A-B, A-C, A-D je 1), dazu B-C 3 und D-E 5. Mit Gradschranke 2 gibt es genau zwei Spannbäume
    (je A-D, D-E und einer der Wege über B-C), Kosten 1 + 5 + 1 + 3 = 10; Greedy nimmt A-B, A-C, lässt A-D aus (Grad), verwirft B-C (Kreis)
    und nimmt D-E: nur 3 von 4 Leitungen, kein Spannbaum."""
    return Instance(POINTS5, ((0, 1, 1), (0, 2, 1), (0, 3, 1), (1, 2, 3), (3, 4, 5)))


@pytest.fixture
def bruecke():
    """4 Standorte: A-B 1, A-C 1, A-D 2, B-C 3, C-D 5. Mit Gradschranke 2 nimmt Greedy A-B, A-C, C-D (Kosten 7); optimal sind A-D, A-B, B-C
    und A-D, A-C, B-C (je Kosten 6)."""
    return Instance(POINTS5[:4], ((0, 1, 1), (0, 2, 1), (0, 3, 2), (1, 2, 3), (2, 3, 5)))
