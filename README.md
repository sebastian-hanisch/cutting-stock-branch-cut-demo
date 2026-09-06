# Branch & Cut am Cutting-Stock-Problem – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-cutting-stock-branch-cut-demo.streamlit.app/)**

Viertes Stück der Cutting-Stock-Linie - die **Konvergenz** von
[cutting-stock-branch-bound-demo](https://github.com/sebastian-hanisch/cutting-stock-branch-bound-demo)
(Verzweigung) und
[cutting-stock-cutting-planes-demo](https://github.com/sebastian-hanisch/cutting-stock-cutting-planes-demo)
(Symmetrie-Schnitt, unverändert übernommen), mirror von
[branch-cut-demo](https://github.com/sebastian-hanisch/branch-cut-demo)s Rolle
in der ersten (Rucksack-)Linie. Dort wurden Cover-Cuts einmalig an der Wurzel
gefunden und dann eingefroren ("Cut-and-Branch") - hier kommt eine **echte,
an jedem Suchbaum-Knoten frisch gelöste LP-Schranke** dazu: echtes,
per-Knoten wiederholtes Branch & Cut.

## Ein wichtiger Designpunkt aus der Planung

Der Symmetrie-Schnitt aus `cutting-stock-cutting-planes-demo` wirkt bereits
an JEDEM Knoten, nicht nur an der Wurzel - er erfüllt die "per-Knoten"-
Anforderung dieser Linie schon von sich aus. Die Konvergenz dieses Stücks
braucht deshalb eine zweite, unabhängige Zutat: eine echte LP-Relaxation
(kompakte Kantorovich-Formulierung), an jedem Knoten neu gelöst - das erste
`scipy`/LP-Vorkommen in dieser Linie.

## Die LP-Schranke

Kompakte Relaxation: Variablen $x_{i,k}$ (Anteil von Stück $i$ in bereits
offenem Bin $k$, nur wenn es dort passt) und $x_{i,\text{neu}}$ plus EINE
aggregierte Schlupfvariable $y_{\text{neu}}$ für den "neue-Bins-Pool" (neue
Bins sind in der Relaxation austauschbar - ein Repräsentant statt vieler
y-Variablen reicht). Anders als `weak_bound` (blinde Summe aus Restbreite
gegen Restkapazität) erzwingt diese Relaxation PRO Bin/Stück-Paar, ob es
überhaupt passt - strenger, wann immer ein Reststück in manche offene Bins
passt, in andere nicht.

**Vor der Umsetzung per Prototyp verifiziert**: über einen breiten Sweep
übertrifft die LP-Schranke `weak_bound` an ~22% der ausgewerteten Knoten.
Kombiniert mit dem Symmetrie-Schnitt reduziert sie die Knotenzahl auf
ausgewählten Instanzen um das 2,4-fache bis über das 168-fache zusätzlich;
bei einer Instanz scheitert sogar die Baseline (ganz ohne Technik) an der
100.000-Knoten-Grenze, während die volle Kombination dieselbe Instanz in
gut 100 Knoten löst. Gegen Bruteforce exakt geprüft, kein Fund einer
Abweichung.

**Ehrliche Grenze**: diese kompakte Relaxation bleibt insgesamt schwach
(bekannter Fakt für Bin Packing, Worst-Case-Verhältnis nahe $n/2$) - die
wirklich starke, Muster-basierte Relaxation (Gilmore-Gomory) kommt erst mit
Column Generation später in dieser Linie.

## Bewiesene statt nur beobachtete Knoten-Reduktion

Anders als beim Symmetrie-Schnitt (der die Verzweigungsstruktur ändert und
dessen Knotenzahl-Monotonie deshalb in `cutting-stock-cutting-planes-demo`
empirisch geprüft werden musste) ändert die LP-Schranke bei sonst
identischer Verzweigung nur den Schrankenwert. Eine punktweise mindestens so
starke gültige Schranke kann nachweislich nie weniger abschneiden als eine
schwächere - `nodes(..., use_lp_bound=True) <= nodes(..., use_lp_bound=False)`
ist deshalb eine bewiesene, nicht nur beobachtete Invariante (trotzdem als
Regressionstest verankert).

## Verifikation

- **Bruteforce-Cross-Check** über alle vier Kombinationen von
  `use_symmetry_cut`/`use_lp_bound`.
- **Schranken-Monotonie-Regressionstest** (bewiesen, siehe oben).
- **LP-Wirksamkeits-Test**: die `lp_margin`-Kennzahl ist auf einer
  bekannten Instanz nachweislich > 0 - keine unbeobachtbare Kennzahl.
- **Dreier-Reduktions-Regressionstest**: Baseline scheitert, nur-Schnitt
  braucht tausende Knoten, Schnitt+LP löst dieselbe Instanz in unter 500.
- **Sicherheitsgrenzen-Test** wie in jedem vorherigen Stück.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Hauptablauf: Presets, Einstellungen, Suchbaum-Animation, Dreier-Vergleich, Formulierungs-Expander |
| `csbc_constants.py` | Defaults, Regler-Grenzen, Sicherheitsgrenzen, `PRESETS` |
| `csbc_presets.py` | `SettingSpec`/`SETTING_SPECS`, Permalink-Logik, Presets, Zufalls-Seed-Button |
| `csbc_scenario.py` | Zufällige Cutting-Stock-Instanzen, Bin-Packing-Brücke |
| `csbc_bounds.py` | `weak_bound`, `lp_bound` (neu, scipy-LP), `combined_bound` |
| `csbc_solver.py` | n-äre Tiefensuche mit Symmetrie-Schnitt und LP-Schranke |
| `csbc_bruteforce.py` | Unabhängige Referenzlösung (vollständige Enumeration) |
| `csbc_evaluation.py` | Kennzahlen, Dreier-Vergleich (Baseline/Schnitt/Schnitt+LP) |
| `csbc_visualization.py` | Suchbaum- und Vergleichsdiagramm (Plotly) |
| `tests/` | Bruteforce-Cross-Check, Schranken-Monotonie, LP-Wirksamkeit, Dreier-Reduktion, Sicherheitsgrenzen |

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

Teil des [Operations-Research-Demo-Portfolios](https://sebastianhanisch.net/demos.html) von
[Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning.
Interesse an einer maßgeschneiderten Lösung? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html).
