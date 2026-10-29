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



# Interval kepercayaan rata-rata satu kelompok (bootstrap persentil, tanpa pasangan)
def mean_ci(values, iterations=2000, confidence=0.95, seed=2906):
    a = np.asarray(values, dtype=float)
    if a.ndim != 1 or a.size == 0:
        raise ValueError("values must be a non-empty 1-D array")
    rng = np.random.default_rng(seed)
    means = np.empty(iterations)
    n = a.size
    # Ambil sampel acak dengan pengembalian sebanyak n, lalu hitung rata-ratanya
    for i in range(iterations):
        idx = rng.integers(0, n, size=n)
        means[i] = a[idx].mean()
    alpha = (1 - confidence) / 2
    return float(a.mean()), tuple(float(x) for x in np.quantile(means, [alpha, 1 - alpha]))
