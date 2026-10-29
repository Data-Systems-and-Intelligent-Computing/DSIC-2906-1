"""B1 — TwoHopSearch, mengikuti Algorithm 1 pada Liu et al. (2026).

Ringkasan Algorithm 1:
- frontier B berisi titik awal dan hanya titik yang memenuhi predikat;
- untuk titik p* yang dikunjungi, setiap tetangga yang belum dikunjungi dievaluasi predikatnya:
  yang lolos masuk B, yang tidak lolos dikumpulkan di U;
- bila |U| > |N_out(p*)| / 2, tetangga dari titik-titik di U (dua-hop) yang belum dikunjungi
  dievaluasi predikatnya dan yang lolos masuk B;
- B dipangkas ke ukuran L_search, menyimpan titik terdekat ke kueri.
"""
from __future__ import annotations

import numpy as np

from src.search.graph_index import Beam, deadline_from, expired


def twohop_search(query: np.ndarray, vectors: np.ndarray, neighbors: list[np.ndarray], start: int,
                  eligible: np.ndarray, k: int = 10, L: int = 100,
                  timeout_ms: float | None = None) -> tuple[list[int], dict]:
    """Penelusuran berfilter dengan perluasan dua-hop (Algorithm 1).

    `eligible` adalah mask boolean seluruh titik (True = memenuhi predikat). Titik awal graf
    dipakai sebagai pintu masuk walaupun tidak memenuhi predikat, tetapi tidak masuk ke hasil.
    """
    deadline = deadline_from(timeout_ms)
    n = len(vectors)
    seen = np.zeros(n, dtype=bool)
    visited = np.zeros(n, dtype=bool)
    evaluated = np.zeros(n, dtype=bool)  # penanda titik yang predikatnya sudah pernah dicek (P4)
    seen[start] = True
    beam = Beam(L, n)
    beam.push(float(1.0 - vectors[start] @ query), start)
    n_visited, n_dist, n_pred, n_twohop = 0, 1, 0, 0

    # Batas waktu dicek sebelum setiap kunjungan; bila habis, penelusuran berhenti dengan hasil parsial
    while not (timed_out := expired(deadline)) and (top := beam.pop_unvisited()) is not None:
        # Titik terdekat di frontier yang belum dikunjungi (baris 3-4)
        _, nxt = top
        visited[nxt] = True
        n_visited += 1

        # Tetangga satu-hop yang belum dikunjungi: lolos -> B, tidak lolos -> U (baris 6-8)
        out = neighbors[nxt]
        one = out[~visited[out]]
        n_pred += len(one)
        evaluated[one] = True
        ok = eligible[one]
        add = [one[ok]]
        U = one[~ok]

        # Perluasan dua-hop bila lebih dari separuh tetangga tidak lolos (baris 9-12)
        if len(U) > len(out) / 2:
            n_twohop += 1
            two = np.unique(np.concatenate([neighbors[u] for u in U]))
            two = two[~visited[two]]
            n_pred += len(two)
            evaluated[two] = True
            add.append(two[eligible[two]])

        # Kandidat baru masuk frontier yang dipangkas ke L (baris 13-14)
        new = np.unique(np.concatenate(add))
        new = new[~seen[new]]
        if len(new):
            seen[new] = True
            d = 1.0 - vectors[new] @ query
            n_dist += len(new)
            for dist, i in zip(d.tolist(), new.tolist()):
                beam.push(dist, i)

    result = [i for _, i in beam.items() if eligible[i]][:k]
    return result, {
        "method": "twohop",
        "L": L,
        "visited_nodes": n_visited,
        "distance_comparisons": n_dist,
        "predicate_evaluations": n_pred,
        "predicate_evaluations_unique": int(evaluated.sum()),
        "twohop_expansions": n_twohop,
        "returned_count": len(result),
        "underfilled": len(result) < k,
        "timeout": timed_out,
    }
