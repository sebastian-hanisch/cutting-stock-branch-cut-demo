"""Unabhängiges Orakel für `lp_bound`: Die kompakte Relaxation (Stücke dürfen beliebig auf offene Bins
verteilt werden, sofern jedes Stück in das Bin passt; Rest geht in den Neu-Bin-Pool) hat den
geschlossenen Wert  y = (Restbreite - maximaler Fluss) / W  mit einem Transportfluss Stück -> Bin
(Kapazität Stück = Breite, Bin = Restkapazität). Hier mit networkx statt HiGHS nachgerechnet, ganzzahlig exakt.
Dazu: Optimum aller vier Solver-Varianten gegen unabhängige Bitmasken-DP."""

import random

import pytest

from csbc_bounds import lp_bound, weak_bound
from csbc_scenario import CuttingStockInstance, expand_pieces
from csbc_solver import solve

nx = pytest.importorskip("networkx")


def _flow_bound(roll_width, rest, bins):
    if not rest:
        return len(bins)
    g = nx.DiGraph()
    for i, p in enumerate(rest):
        g.add_edge("s", ("p", i), capacity=p)
        for k, cap in enumerate(bins):
            if p <= cap:
                g.add_edge(("p", i), ("b", k))
    for k, cap in enumerate(bins):
        g.add_edge(("b", k), "t", capacity=cap)
    flow = nx.maximum_flow_value(g, "s", "t") if "t" in g else 0
    return len(bins) + max(0, -(-(sum(rest) - flow) // roll_width))


def _dp_bins(pieces, width):
    n = len(pieces)
    if n == 0:
        return 0
    inf = (10**9, 0)
    dp = [inf] * (1 << n)
    dp[0] = (1, 0)
    for mask in range(1 << n):
        bins, fill = dp[mask]
        if bins >= 10**9:
            continue
        for i in range(n):
            if mask >> i & 1:
                continue
            cand = (bins, fill + pieces[i]) if fill + pieces[i] <= width else (bins + 1, pieces[i])
            if cand < dp[mask | 1 << i]:
                dp[mask | 1 << i] = cand
    return dp[-1][0]


def _random_instance(rng):
    width = rng.choice([10, 20, 37, 50, 100])
    n_types = rng.randint(1, 4)
    widths = tuple(rng.randint(max(1, round(0.1 * width)), max(2, round(0.7 * width))) for _ in range(n_types))
    demands = tuple(rng.randint(1, 3) for _ in range(n_types))
    return CuttingStockInstance(width, widths, demands)


def test_lp_bound_equals_transport_flow_value_on_random_states():
    rng = random.Random(21)
    strict = 0
    for _ in range(120):
        inst = _random_instance(rng)
        pieces = expand_pieces(inst)
        depth = rng.randint(0, len(pieces) - 1)
        bins = []
        for p in pieces[:depth]:
            fits = [i for i, c in enumerate(bins) if c >= p]
            if fits and rng.random() < 0.7:
                bins[rng.choice(fits)] -= p
            else:
                bins.append(inst.roll_width - p)
        got = lp_bound(inst, pieces, depth, bins)
        assert got == _flow_bound(inst.roll_width, list(pieces[depth:]), bins), (inst, depth, bins)
        assert got >= weak_bound(inst, pieces, depth, bins)
        strict += got > weak_bound(inst, pieces, depth, bins)
    assert strict > 0


@pytest.mark.parametrize("use_symmetry_cut", [False, True])
@pytest.mark.parametrize("use_lp_bound", [False, True])
def test_all_variants_match_bitmask_dp(use_symmetry_cut, use_lp_bound):
    rng = random.Random(5)
    checked = 0
    while checked < 40:
        inst = _random_instance(rng)
        pieces = expand_pieces(inst)
        if len(pieces) > 9:
            continue
        checked += 1
        result = solve(inst, use_symmetry_cut=use_symmetry_cut, use_lp_bound=use_lp_bound)
        assert result.best_value == _dp_bins(pieces, inst.roll_width), inst
