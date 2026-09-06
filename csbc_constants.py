"""Defaults, slider bounds und Presets für die Cutting-Stock-Branch-&-Cut-Demo."""

DEFAULT_N_TYPES = 4
DEFAULT_MAX_DEMAND = 2
DEFAULT_ROLL_WIDTH = 100
DEFAULT_SEED = 7

N_TYPES_MIN, N_TYPES_MAX = 2, 7
MAX_DEMAND_MIN, MAX_DEMAND_MAX = 1, 4
ROLL_WIDTH_MIN, ROLL_WIDTH_MAX = 50, 200

# Auftragsbreiten werden als Anteil der Rollenbreite gezogen - hält die Instanzen
# unabhängig von der absoluten Rollenbreite vergleichbar (wie in den vorherigen
# Stücken dieser Linie).
WIDTH_FRACTION_RANGE = (0.15, 0.6)

# Per Prototyp kalibriert: schon mit Symmetrie-Schnitt allein kann die Baseline
# (ganz ohne Technik) weit über 100.000 Knoten erreichen, während die volle
# Kombination (Schnitt + LP-Schranke) dieselben Instanzen im niedrigen
# dreistelligen Bereich löst. 100.000 deckt jede Preset-Kombination komfortabel
# ab und lässt "LP-Schranke entscheidet" bewusst an der Baseline scheitern.
MAX_NODES_EXPLORED = 100_000
MAX_NODES_RENDERED = 800

PRESETS = {
    "Winzige Instanz (Baum komplett sichtbar)": {
        "n_types": 3, "roll_width": 100, "max_demand": 2, "seed": 9,
    },
    "Alle Zutaten im Vergleich": {
        "n_types": 5, "roll_width": 100, "max_demand": 4, "seed": 3,
    },
    "LP-Schranke entscheidet": {
        "n_types": 7, "roll_width": 100, "max_demand": 3, "seed": 9,
    },
}
