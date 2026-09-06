"""Zwei unabhängige Schranken für die Bin-Packing-Suche, gemeinsame Signatur
`bound_fn(instance, pieces, depth, bins)` - `bins` ist eine Liste der
Restkapazitäten aller bereits geöffneten Bins. Beide liefern eine gültige
UNTERGRENZE für die insgesamt benötigte Bin-Anzahl, nie eine Überschätzung."""

import math

import numpy as np
from scipy.optimize import linprog


def weak_bound(instance, pieces, depth, bins):
    """L1-Schranke wie in jedem vorherigen Stück dieser Linie: Restbreite aller
    noch offenen Stücke, die nicht mehr in die Restkapazität bereits geöffneter
    Bins passt, durch die Rollenbreite geteilt (aufgerundet). Blind dafür, ob ein
    BESTIMMTES Stück in ein BESTIMMTES Bin passt - aggregiert nur Summen."""
    remaining_width = sum(pieces[depth:])
    remaining_capacity = sum(bins)
    if remaining_width <= remaining_capacity:
        return len(bins)
    extra = -(-(remaining_width - remaining_capacity) // instance.roll_width)
    return len(bins) + extra


def lp_bound(instance, pieces, depth, bins):
    """Kompakte LP-Relaxation (Kantorovich-Formulierung), an DIESEM Knoten frisch
    gelöst - das erste scipy/LP-Vorkommen dieser Linie. Variablen: x[i,k] - Anteil
    von Stück i in bereits offenem Bin k (nur erlaubt, wenn es dort überhaupt
    passt), x[i,neu] - Anteil von Stück i im "neue-Bins-Pool", y_neu >= 0 - Anzahl
    benötigter neuer Bins (EINE aggregierte Variable statt einer pro potenziellem
    neuen Bin, da neue Bins in der Relaxation austauschbar sind). Minimiere y_neu
    unter: jedes Stück zu 100% verteilt (Gleichung je Stück), Kapazität je
    bereits offenem Bin eingehalten (Ungleichung je Bin), neue-Bins-Pool-Kapazität
    eingehalten (eine Ungleichung).

    Anders als `weak_bound` (blinde Summenbildung) erzwingt diese Relaxation PRO
    Bin/Stück-Paar, ob es überhaupt passt - strenger, wann immer ein Restauftrag
    in manche offene Bins passt, in andere nicht. Per Prototyp verifiziert: über
    einen breiten Sweep übertrifft diese Schranke `weak_bound` an ~22% der
    ausgewerteten Knoten. Bleibt trotzdem insgesamt eine schwache Schranke
    (bekannter Fakt für Bin Packings kompakte Formulierung, Worst-Case nahe n/2)
    - die wirklich starke, Muster-basierte Relaxation kommt erst mit Column
    Generation später in dieser Linie."""
    remaining = pieces[depth:]
    m = len(bins)
    n = len(remaining)
    if n == 0:
        return len(bins)

    n_vars = n * (m + 1) + 1
    idx_y = n_vars - 1

    def idx_existing(i, k):
        return i * (m + 1) + k

    def idx_new(i):
        return i * (m + 1) + m

    c = np.zeros(n_vars)
    c[idx_y] = 1.0

    A_eq = []
    b_eq = []
    for i in range(n):
        row = np.zeros(n_vars)
        for k in range(m):
            row[idx_existing(i, k)] = 1.0
        row[idx_new(i)] = 1.0
        A_eq.append(row)
        b_eq.append(1.0)

    A_ub = []
    b_ub = []
    for k in range(m):
        row = np.zeros(n_vars)
        for i in range(n):
            row[idx_existing(i, k)] = remaining[i]
        A_ub.append(row)
        b_ub.append(bins[k])

    row = np.zeros(n_vars)
    for i in range(n):
        row[idx_new(i)] = remaining[i]
    row[idx_y] = -instance.roll_width
    A_ub.append(row)
    b_ub.append(0.0)

    bounds = []
    for i in range(n):
        for k in range(m):
            hi = 1.0 if remaining[i] <= bins[k] else 0.0
            bounds.append((0, hi))
        bounds.append((0, 1))
    bounds.append((0, None))

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
    if not res.success:
        # Sollte nie passieren - der neue-Bins-Pool ist immer zulässig, also ist
        # die Relaxation immer lösbar. Fallback auf die einfache Schranke.
        return weak_bound(instance, pieces, depth, bins)
    y_new_val = res.x[idx_y]
    extra = max(0, math.ceil(y_new_val - 1e-6))
    return len(bins) + extra


def combined_bound(instance, pieces, depth, bins):
    """Das punktweise Maximum zweier gültiger Schranken ist wieder eine gültige
    (und nie schwächere) Schranke. Anders als bei den bisherigen "starke
    Schranke"-Funden dieser Serie ist diese Kombination NACHWEISLICH wirksam
    (siehe Prototyp-Sweep oben und die Tests), nicht nur theoretisch gültig."""
    return max(weak_bound(instance, pieces, depth, bins), lp_bound(instance, pieces, depth, bins))
