"""P1 — AdaptiveL, mengikuti Algorithm 2 dan 3 pada Liu et al. (2026).

Ringkasan Algorithm 2:
- penelusuran graf standar: seluruh tetangga titik yang dikunjungi masuk frontier B,
  tanpa memedulikan predikat (navigasi boleh melewati titik yang tidak lolos);
- predikat dievaluasi pada titik yang dikunjungi p*; yang lolos masuk himpunan hasil dan
  menambah n_match;
- B dipangkas ke ukuran L_search;
- ketika jumlah titik dikunjungi |V| = n_sample, L_search dikali ComputeAdaptiveL(n_match / n_sample, m).
  Baris 10 pada paper tertulis "L_search <- L_search" (faktor pengali tidak tercetak); interpretasi
  di sini mengikuti teks bagian 2 dan Algorithm 3.
"""
from __future__ import annotations

import math

import numpy as np

from src.search.graph_index import Beam


def compute_adaptive_multiplier(sp_hat: float, m_max: float) -> float:
    if not 0.0 <= sp_hat <= 1.0:
        raise ValueError("sp_hat must be in [0, 1]")
    if m_max < 1:
        raise ValueError("m_max must be >= 1")
    if sp_hat == 0:
        return float(m_max)
    if sp_hat >= 0.5:
        return 1.0
    if sp_hat >= 0.1:
        return min(float(m_max), 2.0)
    l = -math.log10(sp_hat)
    return min(float(m_max), 2.0 ** l)


def adaptivel_search(query: np.ndarray, vectors: np.ndarray, neighbors: list[np.ndarray], start: int,
                     eligible: np.ndarray, k: int = 10, L: int = 100, n_sample: int = 64,
                     m_max: float = 8) -> tuple[list[int], dict]:
    """Penelusuran greedy dengan ukuran frontier yang menyesuaikan estimasi match rate (Algorithm 2)."""
    seen = np.zeros(len(vectors), dtype=bool)
    seen[start] = True
    beam = Beam(L, len(vectors))
    beam.push(float(1.0 - vectors[start] @ query), start)
    results: list[tuple[float, int]] = []
    n_visited, n_match, n_dist = 0, 0, 1
    sp_hat, multiplier = None, 1.0

    while (top := beam.pop_unvisited()) is not None:
        # Titik terdekat di frontier yang belum dikunjungi (baris 5-6)
        nxt_d, nxt = top
        n_visited += 1

        # Predikat dievaluasi pada titik yang dikunjungi (baris 7)
        if eligible[nxt]:
            n_match += 1
            results.append((nxt_d, nxt))

        # Seluruh tetangga baru masuk frontier yang dipangkas ke L (baris 8-9)
        nb = neighbors[nxt]
        new = nb[~seen[nb]]
        if len(new):
            seen[new] = True
            d = 1.0 - vectors[new] @ query
            n_dist += len(new)
            for dist, i in zip(d.tolist(), new.tolist()):
                beam.push(dist, i)

        # Setelah n_sample titik dikunjungi, L_search diskalakan sekali (baris 10, Algorithm 3)
        if sp_hat is None and n_visited == n_sample:
            sp_hat = n_match / n_sample
            multiplier = compute_adaptive_multiplier(sp_hat, m_max)
            beam.L = int(math.ceil(L * multiplier))

    results.sort()
    result = [i for _, i in results[:k]]
    return result, {
        "method": "adaptivel",
        "L": L,
        "n_sample": n_sample,
        "m_max": m_max,
        "sample_reached": sp_hat is not None,
        "sp_hat": sp_hat,
        "multiplier": multiplier,
        "L_final": beam.L,
        "visited_nodes": n_visited,
        "distance_comparisons": n_dist,
        "predicate_evaluations": n_visited,
        "returned_count": len(result),
        "underfilled": len(result) < k,
    }
