# Greedy und Tausch: warum die Regel gewinnt – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-greedy-austausch-demo.streamlit.app/)** -->

Erstes Stück (Wurzel) der Reihe **Matroide und Submodularität** (Bereich Kombinatorik) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Ein Leitungsnetz soll alle Standorte verbinden, so billig wie möglich: **Greedy** (Kruskal) ordnet die möglichen Leitungen nach Kosten und nimmt jede, die keinen Kreis schließt. Die Demo fragt nicht, *dass* das optimal ist (das zeigt [kruskal-demo](../kruskal-demo) mit Schnitt- und Kreis-Eigenschaft), sondern *woran man es erkennt* und *was kippt*, wenn eine einzige Nebenbedingung dazukommt.

**Einordnung in die Reihe:** Wurzel. Nachfolger ist Stück 2 (Unabhängigkeitssysteme: wo dieselbe Regel scheitert und wie schlimm), danach Stück 3 (das Matroid, die Struktur hinter den Beobachtungen). Nachbarn in der Spannbaum-Reihe: [kruskal-demo](../kruskal-demo) (Ablauf, Union-Find, Umweg-Faktor, Stabilität, Gleichstände), [constrained-mst-demo](../constrained-mst-demo) und [cmst-demo](../cmst-demo) (Lösungsverfahren für Gradschranke und Kapazität; hier nur als Gegenprobe), [mst-sensitivity-demo](../mst-sensitivity-demo) (Fundamentalkreise).

## Warum dieses Problem

Auf dem Spannbaum gewinnt Greedy so verlässlich, dass es auffällt, wenn es einmal nicht gewinnt. Die Demo zeigt **drei Fingerabdrücke**, an denen man Greedy-Verfahren prüfen kann, und eine Nebenbedingung (höchstens drei oder zwei Leitungen je Standort), bei der sie nicht mehr gelten:

1. **Nur die Reihenfolge zählt.** Jede streng wachsende Umrechnung der Kosten lässt den Baum unverändert.
2. **Für jede Größe gleichzeitig optimal.** Die ersten k gewählten Leitungen sind der billigste Wald mit k Leitungen, für jedes k.
3. **Tauschen schadet nie.** Von jedem Spannbaum aus führt verbesserndes Tauschen zum Optimum; es gibt kein falsches lokales Optimum.

Der Grund ist das **Tauschargument**: Legt man zu einem Spannbaum eine Leitung dazu, entsteht genau ein Kreis, und jede teurere Leitung dieses Kreises lässt sich gegen sie tauschen. Dass jeder Tausch einen Partner findet, misst Experiment 5. Die Struktur, die das trägt (das Matroid), gehört zu Stück 3.

## Befunde und Korrekturen gegenüber dem Plan

- **Hook verschoben:** Der Plan (`PLAN-01-greedy-spannbaum.md` im Planungsordner der Linie) nahm als Hook „Greedy ist in 100 % der Fälle optimal“. Das stimmt, ist aber doppelt zu `kruskal-demo`. Der Hook sind die drei Fingerabdrücke und ihr Kippen bei einer Gradschranke.
- **Spielwiese ohne Kostenbearbeitung:** Der Plan sah vor, Kanten und Kosten von Hand zu setzen. Die Spielwiese tauscht nur an den Kosten des Plans; eine eigene Kostentabelle ist nicht gebaut (siehe „Bewusst nicht umgesetzt“).
- **Gradschranke 1 (Paarung) nicht in der App:** Die Vormessung hatte auch Wälder mit höchstens einer Leitung je Standort geprüft. Die App kennt nur die Schranken 3 und 2, weil bei Schranke 1 kein Spannbaum mehr möglich ist (mehr als zwei Standorte).
- **Nicht neu, nur anders eingeordnet:** Dass Kruskal und Prim mit Gradgrenze scheitern (im Wald enden, obwohl ein Baum existiert) und dass Grad 3 auf gleichverteilten Punkten fast nichts kostet, steht schon in [constrained-mst-demo](../constrained-mst-demo). Hier ist es Teil des Kippens der drei Fingerabdrücke; die billige Nabe ist eine bewusste Konstruktion, damit die Schranke 3 überhaupt bindet (ohne Nabe bindet sie auf den 40 festen Plänen nie).
- **Instanzen anders als in der Vormessung:** Die Vormessung nahm zufällige Kosten; die App nimmt Kosten aus Entfernungen auf einem Plan mit Depot in der Mitte. Zahlen aus der Vormessung stehen deshalb hier nicht.

## Modell

Ein Plan hat n Standorte (Knoten A ist das Depot in der Mitte, die übrigen liegen zufällig) und m = min(n(n − 1)/2, 2n − 2) mögliche Leitungen: ein kürzestes Gerüst, damit der Plan zusammenhängt, plus die kürzesten übrigen Paare. Die Kosten einer Leitung sind ihre Länge mal 100, auf ganze Zahlen gerundet. Mit **billiger Nabe** kosten Leitungen am Depot 40 % davon. Gesucht ist ein Spannbaum mit kleinsten Kosten, optional mit höchstens d Leitungen je Standort (d = 3 oder 2). Formeln stehen im 📐-Expander der App.

## Methodik

- **Greedy:** Leitungen nach (Kosten, Index) ordnen, jede nehmen, die keinen Kreis schließt und (mit Schranke) keinen Standort über d bringt (`mtr_algorithm.py`, `greedy_steps`).
- **Prüfer:** Wald und Spannbaum werden mit einer Tiefensuche geprüft, nicht mit dem Union-Find des Greedy (`check_forest`, `check_tree`).
- **Aufzählen:** alle Spannbäume und alle Wälder per Rekursion über die Leitungen (`enumerate_forests`); bei höchstens 16 Leitungen schnell. Daraus: Optimum, Zahl der optimalen Bäume, bester Wald je Größe.
- **Tausch:** neue Leitung hinein, eine teurere Leitung ihres Kreises heraus; Lokalsuche mit zufälligem oder bestem verbessernden Tausch (`improving_swaps`, `local_search`).
- **Fingerabdruck 1:** fünf streng wachsende Umrechnungen der Kosten (hoch 3, Logarithmus, plus 1000, Exponentialfunktion, Wurzel); zum Vergleich der Baum der billigsten Wege vom Depot (Dijkstra).
- **Experimente 4 und 5:** Anteile über feste Instanzen (40 Pläne, Seeds 100000 bis 100039; für Experiment 5 zwölf Pläne mit sieben Standorten).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` und werden dort mit den Funktionen der App nachgerechnet.

| Frage | Befund |
|---|---|
| **Standardfall** (7 Standorte, 12 mögliche Leitungen, Seed 8, keine Schranke): Ist Greedy optimal? | Ja. 180 Spannbäume; Greedy und Optimum kosten beide **156**; genau ein Baum ist optimal. |
| **Fingerabdruck 1** (7 Standorte, ohne Nabe, 40 Pläne, 5 Umrechnungen): Ändert sich der Kruskal-Baum? | In **0 von 200** Vergleichen. Der Baum der billigsten Wege vom Depot ändert sich bei „hoch 3“ in **36** von 40 Plänen, beim Logarithmus in 4, bei „plus 1000“ in 2, bei der Exponentialfunktion in 6, bei der Wurzel in 4. |
| **Fingerabdruck 2** (Standardfall): Ist Greedy für jedes k optimal? | Ja, für alle 6 Größen. |
| **Fingerabdruck 3** (Standardfall, Startbaum 1, zufälliger verbessernder Tausch): Endet das Tauschen im Optimum? | Ja, nach **3** Tauschen von Kosten 220 auf 156. |
| **Preset „Billige Nabe, höchstens 3 Leitungen“** (7 Standorte, Seed 8): Ist Greedy mit Schranke optimal? | Nein: Greedy kostet **126**, das Optimum **115** (Greedy liegt **9,6 %** über dem besten); 152 Spannbäume mit der Schranke. Für k = 5 und k = 6 ist Greedy nicht optimal (bei k = 5: 86 statt 76). |
| **Dasselbe Preset, Startbaum 1:** Endet das Tauschen im Optimum? | Mit zufälligem Tausch **nein**: nach **5** Tauschen bei Kosten **132** (Optimum 115). Mit „bester Tausch“ **ja**, nach 3 Tauschen. Das gilt für diesen einen Start. |
| **Preset „Pfad: höchstens 2 Leitungen“** (7 Standorte, Seed 8, ohne Nabe) | Greedy nimmt nur **5 von 6** nötigen Leitungen und findet keinen Spannbaum, obwohl es **24** gibt (der billigste kostet 162). |
| **Experiment 4, ohne Nabe** (7 Standorte, 40 Pläne, je 3 Tausch-Läufe) | Schranke 3: bindet in **0** von 40 Plänen, Greedy immer optimal, die Tausch-Lokalsuche bleibt in **1** von 120 Läufen vor dem Optimum hängen. Schranke 2 (37 Pläne haben einen Spannbaum): bindet in 30, Greedy findet in **21** keinen Spannbaum und ist in 1 nicht optimal, die Lokalsuche hängt in **56** von 111 Läufen. |
| **Experiment 4, mit billiger Nabe** (7 Standorte, 40 Pläne) | Schranke 3: bindet in **37** von 40 Plänen, Greedy ist in **20** nicht optimal und findet in 5 keinen Spannbaum, die Lokalsuche hängt in **44** von 120 Läufen. Schranke 2: bindet in 37 von 37, Greedy ist in 6 nicht optimal und findet in 22 keinen Spannbaum, die Lokalsuche hängt in 60 von 111 Läufen. Ohne Schranke jeweils 0 Abweichungen. |
| **Experiment 5** (12 Pläne mit 7 Standorten, je 20 Baumpaare): Hat jeder Tausch einen Partner? | Spannbäume: bei **694** Tripeln **0** ohne Partner, auch symmetrisch 0. Spannbäume mit höchstens 3 Leitungen je Standort: 44 von 654 (6,7 %) ohne Partner, 152 (23,2 %) ohne symmetrischen. Pfade: 356 von 616 (57,8 %) ohne Partner, 546 (88,6 %) ohne symmetrischen. |
| **Preset „Größte Instanz (9 Standorte)“** | 1160 Spannbäume, Optimum **127** mit 2 optimalen Bäumen; Greedy findet einen davon. |

## Ehrliche Grenzen

- **Kleine Pläne.** Bis 9 Standorte und höchstens 16 mögliche Leitungen, damit sich alle Bäume aufzählen lassen. „Greedy ist optimal“ ist ein Satz; die Demo misst ihn nur an diesen Plänen und beweist ihn nicht.
- **Die drei Fingerabdrücke sind Beobachtungen.** Auf allen gemessenen Plänen ohne Schranke gilt jeder; ein Beweis ist das nicht.
- **Eine Art Nebenbedingung.** Nur die Gradschranke, nur die Werte 3 und 2. Andere Nebenbedingungen (Farben, Kapazitäten) und andere Verfahren unter einer Schranke (etwa ein klügerer Greedy oder lokale Suche mit mehr Nachbarschaft) sind nicht gemessen. „Greedy mit Gradschranke“ ist die Regel, die die Demo vorführt, nicht jedes Verfahren für das gradbeschränkte Problem.
- **Anteile sind Zählungen über 40 feste Pläne,** nicht Raten für alle Pläne. Pläne ohne Spannbaum unter der Schranke zählen nicht mit; die Tausch-Läufe starten von gleichverteilt gezogenen zulässigen Bäumen, drei je Plan.
- **Der Baum der billigsten Wege** ist ein einziges Gegenbeispiel zu Fingerabdruck 1 (ein Baumproblem, dessen Lösung von den Kostenwerten abhängt), kein Vergleich mit allen Verfahren.
- **Lokale Optima mit Schranke:** Dass die Tausch-Lokalsuche hängen bleibt, gilt für die Nachbarschaft „ein Tausch“; mit größerer Nachbarschaft kann sie weiterkommen. Das ist nicht gemessen.
- **Gleichstände:** Bei gleichen Kosten gibt es oft mehrere beste Bäume; Greedy findet einen davon. „Genau ein optimaler Baum“ im Standardfall ist eine Eigenschaft dieses Plans.
- **Spielwiese:** der Kreis-Tausch von Hand ändert nur den Baum, die Kosten des Plans bleiben fest.

## Verifikation

- **Kern:** Greedy, Tausch und Aufzählen gegen Handrechnung auf drei Mini-Instanzen (`tests/conftest.py`); Randfälle: ein Standort, zwei Standorte, alle Kosten gleich, Stern mit Schranke 2 ohne Spannbaum (`tests/test_edge_cases.py`).
- **Orakel** (`tests/test_oracle_greedy_austausch.py`): Zahl der Spannbäume über den Matrix-Baum-Satz in exakten Brüchen (60 Pläne), Aufzählen aller Kantenmengen mit eigener Kreisprüfung, networkx für den billigsten Spannbaum und die Wegekosten des Baums der billigsten Wege, beste Wälder je Größe über alle Teilmengen.
- **Eigenschaften** (`tests/test_properties.py`): die drei Fingerabdrücke, Invarianz gegen die Reihenfolge der Eingabe, gleiches Ergebnis in zwei Prozessen mit verschiedener Hash-Reihenfolge.
- **Verdikte und Presets:** jeder Zweig und jede Zahl der Verdikte an handgesetzten Werten; jedes Preset zeigt den versprochenen Effekt (`tests/test_verdicts.py`, `tests/test_presets.py`).
- **Zahlen aus dieser README:** `tests/test_claims.py`.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an den Grenzen), Experimente und Spielwiese, Permalink, PDF; Layout (Kopf, Schnellstart, Hervorhebung) und Footer.
- **Umfang:** 119 Tests (`pytest --collect-only -q tests`), seriell etwa zwei Minuten.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche: Greedy in Aktion, Kernfrage, fünf Experimente, Spielwiese, Grenzen, Formeln |
| `mtr_constants.py` | Reglergrenzen, feste Instanzen, Farben, Presets |
| `mtr_scenario.py` | Plan: Standorte, mögliche Leitungen, Kosten |
| `mtr_algorithm.py` | Kern: Greedy, Prüfer, Aufzählen, Tausch, Lokalsuche, Tausch-Eigenschaft |
| `mtr_evaluation.py` | Kennzahlen, Messreihen über feste Instanzen, Verdikte |
| `mtr_visualization.py` | Plan, Kosten über k, Kosten über Tausche |
| `mtr_presets.py` | Permalink, Presets, Zufalls-Seed |
| `mtr_layout.py` | fester Kopf |
| `mtr_pdf_export.py` | PDF des aktuellen Plans |
| `tests/` | Kern, Orakel, Eigenschaften, Verdikte, Presets, Claims, Randfälle, Oberfläche, Layout, Footer, Importe |

## Bewusst nicht umgesetzt

- Eigene Kosten von Hand setzen (Kostentabelle) in der Spielwiese.
- Andere Nebenbedingungen als die Gradschranke (Farben, Kapazitäten), Gradschranke 1.
- Pläne über 9 Standorte; Aufzählen wird dort unbequem, und eine Messung am großen Plan wäre keine Aufzählung mehr.
- Der Beweis des Greedy-Satzes und der Begriff des Matroids (Stück 3 und 5).
- Erklärseite „verständlich erklärt“ und Website-Einbindung (erst mit der vollständigen Linie).

## Lokal ausführen

```bash
pip install -r requirements.txt
streamlit run app.py
```

Tests: `pip install -r requirements-dev.txt`, dann `python -m pytest tests -q`. Die CI läuft mit Python 3.12 (`.github/workflows/tests.yml`); die in Streamlit Cloud eingestellte Python-Version ist beim Deploy zu nennen.

Gebaut mit Streamlit, Plotly und fpdf2.

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
