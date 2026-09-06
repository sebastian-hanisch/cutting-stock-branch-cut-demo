"""Kennzahlen aus einem Suchlauf, plus der Kern-Vergleich dieses Stücks: derselbe
Suchlauf in drei Ausbaustufen - Baseline (keine Technik), nur Symmetrie-Schnitt
(entspricht cutting-stock-cutting-planes-demo), Symmetrie-Schnitt + LP-Schranke
(dieses Stück) - auf EXAKT derselben Instanz."""

from collections import Counter

from csbc_constants import MAX_NODES_EXPLORED
from csbc_solver import solve


def compute_stats(result):
    counts = Counter(node.status for node in result.nodes)
    return {
        "nodes_explored": len(result.nodes),
        "pruned_bound": counts["prune_bound"],
        "leaves_evaluated": counts["leaf_new_best"] + counts["leaf_not_best"],
        "skipped_symmetric_total": sum(n.skipped_symmetric for n in result.nodes),
        "lp_margin_total": sum(n.lp_margin for n in result.nodes),
        "best_value": result.best_value,
        "truncated": result.truncated,
    }


def stats_up_to_step(result, step):
    relevant = [node for node in result.nodes if node.id <= step]
    counts = Counter(node.status for node in relevant)
    current_best = None
    for nid, v in result.incumbent_history:
        if nid <= step:
            current_best = v
    return {
        "nodes_so_far": counts.total(),
        "pruned_bound": counts["prune_bound"],
        "skipped_symmetric_so_far": sum(n.skipped_symmetric for n in relevant),
        "lp_margin_so_far": sum(n.lp_margin for n in relevant),
        "current_best": current_best,
    }


def three_way_comparison(instance, max_nodes=MAX_NODES_EXPLORED):
    baseline = solve(instance, use_symmetry_cut=False, use_lp_bound=False, max_nodes=max_nodes)
    cut_only = solve(instance, use_symmetry_cut=True, use_lp_bound=False, max_nodes=max_nodes)
    full = solve(instance, use_symmetry_cut=True, use_lp_bound=True, max_nodes=max_nodes)
    return {
        "baseline_nodes": len(baseline.nodes),
        "baseline_best": baseline.best_value,
        "baseline_truncated": baseline.truncated,
        "cut_only_nodes": len(cut_only.nodes),
        "cut_only_best": cut_only.best_value,
        "cut_only_truncated": cut_only.truncated,
        "full_nodes": len(full.nodes),
        "full_best": full.best_value,
        "full_truncated": full.truncated,
    }
