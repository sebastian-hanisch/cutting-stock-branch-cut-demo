import pytest

from csbc_bruteforce import solve_bruteforce
from csbc_constants import PRESETS
from csbc_scenario import CuttingStockInstance, expand_pieces, generate_instance
from csbc_solver import solve


def _check_solution_feasible(instance, result):
    pieces = expand_pieces(instance)
    assert sum(instance.roll_width - cap for cap in result.best_bins) == sum(pieces)
    for cap in result.best_bins:
        assert 0 <= cap <= instance.roll_width


def test_matches_hand_computed_example():
    instance = CuttingStockInstance(roll_width=10, item_widths=(6,), item_demands=(3,))
    result = solve(instance, use_symmetry_cut=True, use_lp_bound=True)
    assert result.best_value == 3
    assert solve_bruteforce(instance) == 3


@pytest.mark.parametrize("use_symmetry_cut", [True, False])
@pytest.mark.parametrize("use_lp_bound", [True, False])
def test_matches_bruteforce_across_all_combinations(use_symmetry_cut, use_lp_bound):
    for seed in range(15):
        instance = generate_instance(n_types=3, roll_width=100, max_demand=2, seed=seed)
        result = solve(instance, use_symmetry_cut=use_symmetry_cut, use_lp_bound=use_lp_bound)
        true_min = solve_bruteforce(instance)
        assert result.best_value == true_min, (
            f"seed={seed} use_symmetry_cut={use_symmetry_cut} use_lp_bound={use_lp_bound}"
        )
        _check_solution_feasible(instance, result)


@pytest.mark.parametrize("use_symmetry_cut", [True, False])
def test_lp_bound_never_visits_more_nodes_than_without_it(use_symmetry_cut):
    # Bewiesen, nicht nur beobachtet (siehe app.py's Formulierungs-Abschnitt):
    # eine punktweise mindestens so starke gültige Schranke kann bei sonst
    # identischer Verzweigung nie mehr Knoten übrig lassen als eine schwächere.
    for n_types in range(2, 7):
        for max_demand in range(1, 5):
            for seed in range(8):
                instance = generate_instance(n_types, 100, max_demand, seed)
                without_lp = solve(instance, use_symmetry_cut=use_symmetry_cut, use_lp_bound=False, max_nodes=50_000)
                with_lp = solve(instance, use_symmetry_cut=use_symmetry_cut, use_lp_bound=True, max_nodes=50_000)
                if without_lp.truncated:
                    continue
                assert len(with_lp.nodes) <= len(without_lp.nodes), (
                    f"n={n_types} d={max_demand} seed={seed} use_symmetry_cut={use_symmetry_cut}: "
                    f"with_lp={len(with_lp.nodes)} without_lp={len(without_lp.nodes)}"
                )
                assert with_lp.best_value == without_lp.best_value


def test_lp_margin_metric_is_nonzero_on_a_real_instance():
    # Keine unbeobachtbare Geister-Kennzahl: auf einer Instanz, bei der die
    # LP-Schranke bekanntermaßen hilft, muss die Summe der lp_margin-Werte > 0
    # sein.
    instance = generate_instance(**PRESETS["Alle Zutaten im Vergleich"])
    result = solve(instance, use_symmetry_cut=True, use_lp_bound=True)
    assert sum(n.lp_margin for n in result.nodes) > 0


def test_three_way_reduction_regression():
    # Regressionstest für das dritte Preset: Baseline scheitert an der
    # Sicherheitsgrenze, nur-Schnitt braucht noch tausende Knoten, Schnitt+LP
    # löst dieselbe Instanz in unter 500 Knoten.
    instance = generate_instance(**PRESETS["LP-Schranke entscheidet"])
    baseline = solve(instance, use_symmetry_cut=False, use_lp_bound=False, max_nodes=100_000)
    cut_only = solve(instance, use_symmetry_cut=True, use_lp_bound=False, max_nodes=100_000)
    full = solve(instance, use_symmetry_cut=True, use_lp_bound=True, max_nodes=100_000)
    assert baseline.truncated
    assert not cut_only.truncated and len(cut_only.nodes) > 5_000
    assert not full.truncated and len(full.nodes) < 500
    assert cut_only.best_value == full.best_value == solve_bruteforce(instance)


def test_max_nodes_cap_is_honored_and_flagged_as_truncated():
    instance = generate_instance(n_types=7, roll_width=100, max_demand=4, seed=1)
    result = solve(instance, use_symmetry_cut=False, use_lp_bound=False, max_nodes=30)
    assert len(result.nodes) <= 30 + 30  # Sicherheitsmarge für den letzten unvollständigen Options-Batch
    assert result.truncated


@pytest.mark.parametrize("name", list(PRESETS.keys()))
def test_presets_solve_correctly_with_full_combination(name):
    instance = generate_instance(**PRESETS[name])
    result = solve(instance, use_symmetry_cut=True, use_lp_bound=True, max_nodes=100_000)
    assert not result.truncated
    true_min = solve_bruteforce(instance)
    assert result.best_value == true_min, name
