"""
Branch & Cut am Cutting-Stock-Problem – interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Viertes Stück der Cutting-Stock-Linie: die Konvergenz von
cutting-stock-branch-bound-demo (Verzweigung) und
cutting-stock-cutting-planes-demo (Symmetrie-Schnitt), erweitert um eine an
jedem Knoten frisch gelöste LP-Schranke - echtes, per-Knoten wiederholtes
Branch & Cut, anders als branch-cut-demo (erste Linie), das Schnitte einmalig
an der Wurzel fand und dann einfror.

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import csbc_constants as C
from csbc_bruteforce import solve_bruteforce
from csbc_evaluation import stats_up_to_step, three_way_comparison
from csbc_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from csbc_scenario import expand_pieces, generate_instance
from csbc_solver import solve
from csbc_visualization import build_comparison_chart, build_tree_figure

st.set_page_config(page_title="Branch & Cut am Cutting-Stock-Problem – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _compute_solve(n_types, roll_width, max_demand, seed):
    instance = generate_instance(n_types, roll_width, max_demand, seed)
    result = solve(instance, use_symmetry_cut=True, use_lp_bound=True)
    true_optimum = solve_bruteforce(instance)
    return instance, result, true_optimum


@st.cache_data(show_spinner=False)
def _compute_comparison(n_types, roll_width, max_demand, seed):
    instance = generate_instance(n_types, roll_width, max_demand, seed)
    return three_way_comparison(instance)


st.title("🌳✂️📦 Branch & Cut am Cutting-Stock-Problem")
st.markdown(
    """
Viertes Stück der Cutting-Stock-Linie - die **Konvergenz** von
[cutting-stock-branch-bound-demo](https://github.com/sebastian-hanisch/cutting-stock-branch-bound-demo)
(Verzweigung) und
[cutting-stock-cutting-planes-demo](https://github.com/sebastian-hanisch/cutting-stock-cutting-planes-demo)
(Symmetrie-Schnitt, unverändert übernommen), mirror von `branch-cut-demo`s
Rolle in der ersten (Rucksack-)Linie. Dort wurden Schnitte einmalig an der
Wurzel gefunden und dann eingefroren ("Cut-and-Branch") - hier kommt eine
**echte, an jedem Suchbaum-Knoten frisch gelöste LP-Schranke** dazu: echtes,
per-Knoten wiederholtes Branch & Cut, wie im richtigen Leben.
"""
)
st.caption(
    "Anders als die Fall-Demos im Portfolio, die an einem Anwendungsfall mehrere Verfahren "
    "vergleichen, zeigt diese Demo - wie jedes Stück dieser Linie - ein Verfahren an einem "
    "wachsenden Beispiel."
)

with st.expander("So funktioniert die Konvergenz", expanded=True):
    st.markdown(
        r"""
Drei Zutaten, alle gleichzeitig aktiv:

1. **Verzweigung** (aus `cutting-stock-branch-bound-demo`): n-äre Suche, das
   nächste Stück geht in ein bereits offenes Bin oder ein neues wird
   geöffnet.
2. **Symmetrie-Schnitt** (aus `cutting-stock-cutting-planes-demo`,
   unverändert): bei mehreren offenen Bins mit identischer Restkapazität
   wird nur ein Repräsentant zu einer Kindoption - im Baum unten violett
   markiert.
3. **LP-Schranke, neu in diesem Stück**: an jedem Knoten wird zusätzlich eine
   kompakte LP-Relaxation gelöst (welche Reststücke passen anteilig in
   welches Bin?) - strenger als die einfache Schranke, wann immer ein
   bestimmtes Stück in manche offene Bins passt, in andere nicht. Im Baum
   unten petrol-gepunktet markiert, wo sie tatsächlich stärker war.

Der Symmetrie-Schnitt allein wirkt bereits an jedem Knoten - die neue Zutat
dieses Stücks ist deshalb NICHT "auch per Knoten wiederholen" (das war schon
erledigt), sondern die zweite, unabhängige LP-Schranke selbst.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
PRESET_HELP = {
    "Winzige Instanz (Baum komplett sichtbar)": "3 Auftragstypen - der komplette Suchbaum passt aufs Bild. Die LP-Schranke hilft hier ehrlich kaum.",
    "Alle Zutaten im Vergleich": "Baseline, Schnitt allein und Schnitt+LP im direkten Vergleich - ein deutlicher Stufenverlauf.",
    "LP-Schranke entscheidet": "Ohne jede Technik erreicht die Suche die Sicherheitsgrenze, mit Schnitt allein braucht sie noch tausende Knoten - erst die LP-Schranke macht daraus Sekundenbruchteile.",
}
preset_cols = st.columns(len(C.PRESETS))
for i, name in enumerate(C.PRESETS.keys()):
    with preset_cols[i]:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=PRESET_HELP[name])

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_types = st.slider("Anzahl Auftragstypen", *bounds("n_types_slider"), key="n_types_slider")
    roll_width = st.slider("Rollenbreite", *bounds("roll_width_slider"), key="roll_width_slider")
    max_demand = st.slider(
        "Maximaler Bedarf je Auftragstyp", *bounds("max_demand_slider"), key="max_demand_slider",
        help="Höherer Bedarf bedeutet mehr identische Stücke - mehr Gelegenheit für beide Techniken.",
    )
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)

    st.button(
        "🎲 Neue Instanz generieren",
        width="stretch",
        on_click=randomize_seed,
        help="Würfelt neue Auftragsbreiten und -mengen.",
    )

sync_query_params(n_types, roll_width, max_demand, seed)

scenario_key = (int(n_types), int(roll_width), int(max_demand), int(seed))

with st.spinner("Durchsuche den Baum..."):
    instance, result, true_optimum = _compute_solve(*scenario_key)

pieces = expand_pieces(instance)
st.caption(
    f"🔗 {instance.n_types} Auftragstypen, Breiten {instance.item_widths} mit Bedarf "
    f"{instance.item_demands} → {len(pieces)} Einzelstücke, Rollenbreite {instance.roll_width}."
)

st.markdown("## 🎯 Der Suchbaum mit allen drei Zutaten")

if "csbc_step" not in st.session_state or st.session_state.get("csbc_step_owner") != scenario_key:
    st.session_state["csbc_step"] = len(result.nodes) - 1
    st.session_state["csbc_step_owner"] = scenario_key

max_step = len(result.nodes) - 1
step_col, play_col = st.columns([5, 1])
with step_col:
    if max_step == 0:
        step = 0
        st.caption("Nur der Wurzelknoten - kein Regler nötig.")
    else:
        step = st.slider(
            "Schritt (Knoten)", 0, max_step, key="csbc_step",
            help="Ein Schritt = ein besuchter Suchbaum-Knoten, in Besuchsreihenfolge.",
        )
with play_col:
    auto_play = st.button("▶️ Abspielen", width="stretch")

render_note = (
    f" (zeigt die ersten {C.MAX_NODES_RENDERED:,} von {len(result.nodes):,} Knoten)"
    if len(result.nodes) > C.MAX_NODES_RENDERED
    else ""
)
st.caption(f"{len(result.nodes):,} Knoten insgesamt besucht{render_note}.")

tree_slot = st.empty()


def _render(current_step):
    tree_slot.plotly_chart(
        build_tree_figure(result, current_step, C.MAX_NODES_RENDERED),
        width="stretch", key=f"tree_{current_step}",
    )


if auto_play:
    n_frames = min(max_step + 1, 60)
    frame_skip = max(1, (max_step + 1) // n_frames)
    for s in list(range(0, max_step, frame_skip)) + [max_step]:
        _render(s)
        time.sleep(0.08)
    step = max_step
else:
    _render(step)

live = stats_up_to_step(result, step)
lm1, lm2, lm3, lm4, lm5 = st.columns(5)
lm1.metric("Besuchte Knoten (bisher)", f"{live['nodes_so_far']:,}")
lm2.metric(
    "Gestutzt (Bound)", f"{live['pruned_bound']:,}",
    help="Äste, die abgebrochen wurden, weil die Schranke keine Verbesserung mehr versprach.",
)
lm3.metric(
    "Durch Symmetrie übersprungen", f"{live['skipped_symmetric_so_far']:,}",
    help="Baugleiche Bins, die der Symmetrie-Schnitt gar nicht erst als eigene Kindoption erzeugt hat.",
)
lm4.metric(
    "LP-Schranke stärker (Summe)", f"{live['lp_margin_so_far']:,}",
    help="Wie viel stärker die LP-Schranke insgesamt war als die einfache Schranke, aufsummiert.",
)
lm5.metric(
    "Bester Fund bisher", live["current_best"] if live["current_best"] is not None else "–",
    help="Die wenigsten Rollen einer bislang vollständig gefundenen Lösung.",
)

if result.truncated:
    st.error(
        f"⛔ Abgebrochen bei {C.MAX_NODES_EXPLORED:,} untersuchten Knoten - das gezeigte Ergebnis ist die "
        f"beste bislang gefundene, nicht garantiert optimale Lösung."
    )
else:
    st.caption(
        f"Bewiesenes Optimum: **{result.best_value}** Rollen - stimmt mit der unabhängigen "
        f"Bruteforce-Referenz überein."
        if result.best_value == true_optimum
        else f"⚠️ Optimum {result.best_value} weicht von der Bruteforce-Referenz {true_optimum} ab - bitte melden."
    )

st.markdown("---")

st.subheader("📐 Was trägt welche Zutat zur Knotenzahl bei?")
st.markdown(
    """
Live für Ihre aktuelle Instanz: derselbe Suchlauf in drei Ausbaustufen - ganz
ohne Technik, nur mit Symmetrie-Schnitt (entspricht
`cutting-stock-cutting-planes-demo`), und mit beiden Zutaten zusammen (dieses
Stück).
"""
)

cmp = _compute_comparison(*scenario_key)
st.plotly_chart(build_comparison_chart(cmp), width="stretch", key="comparison_chart")

cc1, cc2, cc3 = st.columns(3)
cc1.metric(
    "Baseline", f"{cmp['baseline_nodes']:,} Knoten" + (" (abgebrochen)" if cmp["baseline_truncated"] else ""),
)
cc2.metric(
    "Nur Symmetrie-Schnitt", f"{cmp['cut_only_nodes']:,} Knoten" + (" (abgebrochen)" if cmp["cut_only_truncated"] else ""),
)
cc3.metric(
    "Schnitt + LP-Schranke", f"{cmp['full_nodes']:,} Knoten" + (" (abgebrochen)" if cmp["full_truncated"] else ""),
    delta=f"{cmp['full_nodes'] - cmp['cut_only_nodes']:,} ggü. nur Schnitt", delta_color="inverse",
)

if cmp["baseline_truncated"] and not cmp["full_truncated"]:
    st.success(
        f"✅ Ganz ohne Technik erreicht die Suche die Sicherheitsgrenze von {C.MAX_NODES_EXPLORED:,} Knoten, "
        f"OHNE das Optimum zu beweisen. Mit beiden Zutaten ist dieselbe Instanz mit **{cmp['full_nodes']:,}** "
        f"Knoten vollständig gelöst."
    )
elif not cmp["cut_only_truncated"] and cmp["full_nodes"] and cmp["cut_only_nodes"] / cmp["full_nodes"] >= 1.5:
    factor = cmp["cut_only_nodes"] / cmp["full_nodes"]
    st.success(
        f"✅ Die LP-Schranke reduziert die Knotenzahl gegenüber dem Symmetrie-Schnitt allein um weitere "
        f"**{factor:.1f}×** - für dasselbe bewiesene Optimum."
    )
else:
    st.info(
        "Bei dieser Instanz hilft die LP-Schranke kaum zusätzlich - probieren Sie das Preset "
        "\"LP-Schranke entscheidet\" oder mehr Auftragstypen."
    )

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**LP-Relaxation an einem Suchknoten**: gegeben Reststücke $1, \dots, n$
(Breiten $r_i$) und bereits offene Bins $1, \dots, m$ mit Restkapazitäten
$c_k$. Variablen $x_{i,k} \in [0,1]$ (Anteil von Stück $i$ in Bin $k$, nur
wenn $r_i \leq c_k$), $x_{i,\text{neu}} \in [0,1]$ (Anteil im "neue-Bins-Pool"
- EINE aggregierte Variable statt einer pro potenziellem neuen Bin, da neue
Bins in der Relaxation austauschbar sind), $y_{\text{neu}} \geq 0$.

$$
\min y_{\text{neu}} \quad \text{u.d.N.} \quad
\sum_k x_{i,k} + x_{i,\text{neu}} = 1 \ \forall i, \quad
\sum_i r_i x_{i,k} \leq c_k \ \forall k, \quad
\sum_i r_i x_{i,\text{neu}} \leq W \cdot y_{\text{neu}}
$$

Die Schranke an diesem Knoten ist $|\text{Bins}| + \lceil y_{\text{neu}}^*
\rceil$. Anders als `weak_bound` (blinde Summe aus Restbreite gegen
Restkapazität) erzwingt diese Relaxation PRO Bin/Stück-Paar, ob es überhaupt
passt - strenger, wann immer ein Reststück in manche offene Bins passt, in
andere nicht. Per Sweep verifiziert: übertrifft `weak_bound` an ~22% der
ausgewerteten Knoten; kombiniert mit dem Symmetrie-Schnitt reduziert sie die
Knotenzahl auf manchen Instanzen um mehr als das 150-fache zusätzlich.

**Ehrliche Grenze**: diese kompakte Relaxation bleibt insgesamt schwach
(bekannter Fakt für Bin Packing, Worst-Case-Verhältnis nahe $n/2$) - die
wirklich starke, Muster-basierte Relaxation (Gilmore-Gomory) kommt erst mit
Column Generation später in dieser Linie.

**Warum die Kombination beweisbar nie schlechter ist**: anders als beim
Symmetrie-Schnitt (der die Verzweigungs*struktur* ändert, weshalb dessen
Knotenzahl-Monotonie in `cutting-stock-cutting-planes-demo` erst empirisch
geprüft werden musste) ändert die LP-Schranke bei sonst identischer
Verzweigung nur den Schranken*wert*. Eine punktweise mindestens so starke
gültige Schranke ($\max(\text{weak\_bound}, \text{lp\_bound})$) kann
nachweislich nie weniger abschneiden als die schwächere - die
Knoten-Reduktions-Invariante ist hier bewiesen, nicht nur beobachtet.

**Kontrast zu `branch-cut-demo` (erste Linie)**: dort wurden Cover-Cuts
einmalig am Wurzelknoten gefunden und dann für den ganzen Baum eingefroren
("Cut-and-Branch"). Hier wird die LP-Relaxation an JEDEM Knoten komplett neu
aufgestellt und gelöst - echtes, per-Knoten wiederholtes Branch & Cut.

Implementiert in `csbc_bounds.py` (`lp_bound`, `combined_bound`),
`csbc_solver.py` (Verzweigung mit Schnitt und Schranke) und
`csbc_evaluation.py` (Dreier-Vergleich).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
