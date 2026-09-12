"""Exact filtered kNN oracle for Recall@k evaluation."""
from __future__ import annotations
import numpy as np


def exact_filtered_knn(base: np.ndarray, query: np.ndarray, eligible_mask: np.ndarray, k: int = 10, metric: str = "cosine") -> np.ndarray:
    ids = np.flatnonzero(eligible_mask)
    if ids.size < k:
        raise ValueError(f"Need at least k={k} eligible points; got {ids.size}")
    x = base[ids]
    q = query
    if metric == "cosine":
        xnorm = np.linalg.norm(x, axis=1)
        qnorm = np.linalg.norm(q)
        denom = np.maximum(xnorm * qnorm, 1e-12)
        dist = 1.0 - (x @ q) / denom
    elif metric in {"l2", "euclidean"}:
        dist = np.sum((x - q) ** 2, axis=1)
    else:
        raise ValueError(f"Unsupported metric: {metric}")
    order = np.argpartition(dist, k - 1)[:k]
    order = order[np.argsort(dist[order])]
    return ids[order]
