"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 6, 9, 7           # Standorte inklusive Depot (Knoten A); bis 9, damit das Aufzählen aller Spannbäume schnell bleibt
SEED_MAX, DEFAULT_SEED = 999999, 8
GRADE_OFF = 0                               # Höchstgrad 0 heißt: keine Gradschranke
GRADE_CHOICES = (0, 3, 2)                   # aus, höchstens 3, höchstens 2 Leitungen je Standort
HUB_FACTOR = 0.4                            # mit billiger Nabe kosten Leitungen am Depot (Knoten A) nur 40 % der Entfernung
COST_SCALE = 100                            # Kosten = Entfernung auf dem Plan (0 bis 1,41) mal 100, auf ganze Zahlen gerundet
SWEEP_SEEDS = tuple(range(100000, 100040))  # 40 feste Instanzen für alle Anteile: nie ein einzelner Seed als Befund
LOCAL_STARTS = 3                            # Startbäume je Instanz für die Tausch-Lokalsuche
DEFAULT_START = 1                           # erster Startbaum von Experiment 3 (auf dem Standardplan mit Schranke 3 und billiger Nabe bleibt er hängen)
AXIOM_N = 7                                 # Größe der Instanzen für die Tausch-Eigenschaft
AXIOM_SEEDS = tuple(range(100100, 100112))  # 12 feste Instanzen
AXIOM_PAIRS = 20                            # Baumpaare je Instanz
TRANSFORMS = ("hoch 3", "Logarithmus", "plus 1000", "Exponentialfunktion", "Wurzel")

COLOR_TAKEN = "#2F6B65"
COLOR_REJECTED = "#c0392b"
COLOR_OTHER = "rgba(150,150,150,0.55)"
COLOR_IN = "#1b9e77"
COLOR_OUT = "#d95f02"
COLOR_NODE = "#4c78a8"
COLOR_DEPOT = "#f0a30a"
COLOR_LINE = "#4c78a8"
COLOR_LINE2 = "#d95f02"

PRESETS = {
    "Standardfall (Voreinstellung)": {"n": DEFAULT_N, "seed": DEFAULT_SEED, "nabe": False, "grad": GRADE_OFF},
    "Billige Nabe, höchstens 3 Leitungen": {"n": DEFAULT_N, "seed": DEFAULT_SEED, "nabe": True, "grad": 3},
    "Pfad: höchstens 2 Leitungen": {"n": DEFAULT_N, "seed": DEFAULT_SEED, "nabe": False, "grad": 2},
    "Größte Instanz (9 Standorte)": {"n": N_MAX, "seed": DEFAULT_SEED, "nabe": True, "grad": GRADE_OFF},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "Sieben Standorte, keine Gradschranke: die Welt, in der Greedy gewinnt.",
    "Billige Nabe, höchstens 3 Leitungen": "Leitungen am Depot sind billig, aber am Depot dürfen höchstens drei Leitungen enden: dieselbe Regel, die Schranke bindet.",
    "Pfad: höchstens 2 Leitungen": "An keinem Standort enden mehr als zwei Leitungen, der Baum wird zum Pfad.",
    "Größte Instanz (9 Standorte)": "Neun Standorte, billige Nabe, keine Schranke: so viele Bäume, wie die Aufzählung noch bequem schafft.",
}
