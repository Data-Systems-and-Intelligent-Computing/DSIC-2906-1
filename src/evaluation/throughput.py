"""Queries-per-second utility."""
from __future__ import annotations


def qps(n_queries: int, elapsed_seconds: float) -> float:
    if elapsed_seconds <= 0:
        raise ValueError("elapsed_seconds must be positive")
    return n_queries / elapsed_seconds
