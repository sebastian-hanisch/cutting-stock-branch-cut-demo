"""Erschöpfende Referenzlösung für Bin Packing - unabhängig von der Branch-&-Cut-
Suche, nur für kleine Instanzen praktikabel. Identisch zu den Bruteforce-Referenzen
in jedem vorherigen Stück dieser Linie."""

from csbc_scenario import expand_pieces


def solve_bruteforce(instance):
    pieces = expand_pieces(instance)
    n = len(pieces)
    best = {"count": n}  # triviale obere Schranke: ein Bin pro Stück

    def assign(idx, bins):
        if len(bins) >= best["count"]:
            return
        if idx == n:
            best["count"] = min(best["count"], len(bins))
            return
        piece = pieces[idx]
        for i, cap in enumerate(bins):
            if cap >= piece:
                bins[i] -= piece
                assign(idx + 1, bins)
                bins[i] += piece
        bins.append(instance.roll_width - piece)
        assign(idx + 1, bins)
        bins.pop()

    assign(0, [])
    return best["count"]
