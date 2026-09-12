"""Paired bootstrap skeleton for query-filter level comparisons."""
from __future__ import annotations
import numpy as np


def paired_mean_diff_ci(a, b, iterations=2000, confidence=0.95, seed=2906):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    if a.shape != b.shape or a.ndim != 1 or a.size == 0:
        raise ValueError("a and b must be non-empty paired 1-D arrays")
    rng = np.random.default_rng(seed)
    diffs = np.empty(iterations)
    n = a.size
    for i in range(iterations):
        idx = rng.integers(0, n, size=n)
        diffs[i] = np.mean(a[idx] - b[idx])
    alpha = (1 - confidence) / 2
    return float(np.mean(a-b)), tuple(np.quantile(diffs, [alpha, 1-alpha]))
