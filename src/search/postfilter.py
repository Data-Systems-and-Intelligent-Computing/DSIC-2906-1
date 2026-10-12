"""B0 — Naive ANN + post-filtering (README bagian 18)."""
from __future__ import annotations

import numpy as np

from src.search.graph_index import greedy_search


def postfilter(candidate_ids, predicate, metadata_by_id, k: int = 10):
    out = []
    for idx in candidate_ids:
        if predicate(metadata_by_id[idx]):
            out.append(idx)
            if len(out) == k:
                break
    return out


def postfilter_search(query: np.ndarray, vectors: np.ndarray, neighbors: list[np.ndarray], start: int,
                      eligible: np.ndarray, k: int = 10, candidate_budget: int = 100) -> tuple[list[int], dict]:
    """Penelusuran tanpa filter dengan L = candidate_budget, lalu predikat diterapkan pada kandidat.

    `eligible` adalah mask boolean untuk seluruh titik (True = memenuhi predikat), sama dengan
    yang dipakai ground truth eksak. Bila kandidat yang lolos predikat < k, hasilnya under-filled.
    """
    pool, stats = greedy_search(query, vectors, neighbors, start, L=max(candidate_budget, k))
    candidate_ids = [i for _, i in pool]
    result = [i for i in candidate_ids if eligible[i]][:k]

    stats.update({
        "method": "postfilter",
        "candidate_budget": candidate_budget,
        "predicate_evaluations": len(candidate_ids),
        "returned_count": len(result),
        "underfilled": len(result) < k,
    })
    return result, stats