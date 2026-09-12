"""Utilities for empirical filter match-rate calculation and binning."""
from __future__ import annotations


def match_rate(n_matching: int, n_total: int) -> float:
    if n_total <= 0:
        raise ValueError("n_total must be positive")
    return n_matching / n_total
