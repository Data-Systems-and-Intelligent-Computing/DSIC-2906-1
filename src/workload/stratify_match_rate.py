"""Utilities for empirical filter match-rate calculation and binning."""
from __future__ import annotations

import pandas as pd


def match_rate(n_matching: int, n_total: int) -> float:
    if n_total <= 0:
        raise ValueError("n_total must be positive")
    return n_matching / n_total


# Penempatan match rate (dalam persen) ke bin; batas bawah inklusif, batas atas eksklusif
def assign_bin(match_rate_pct, boundaries_pct: list[float], labels: list[str]):
    if len(boundaries_pct) != len(labels) + 1:
        raise ValueError("boundaries_pct harus satu lebih banyak dari labels")
    return pd.cut(pd.Series(match_rate_pct, dtype=float), bins=boundaries_pct, labels=labels,
                  right=False, include_lowest=True).astype(str).to_numpy()
