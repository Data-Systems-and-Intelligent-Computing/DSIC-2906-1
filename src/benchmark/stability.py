"""Repeated-query top-k overlap metric."""
from __future__ import annotations


def result_overlap(a, b) -> float:
    sa, sb = set(a), set(b)
    denom = max(len(sa), len(sb), 1)
    return len(sa & sb) / denom
