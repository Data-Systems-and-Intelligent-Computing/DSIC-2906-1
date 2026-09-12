"""Latency summaries."""
from __future__ import annotations
import numpy as np


def summarize_latency_ms(values) -> dict:
    a = np.asarray(list(values), dtype=float)
    if a.size == 0:
        raise ValueError("latency values cannot be empty")
    return {"p50_ms": float(np.percentile(a, 50)), "p95_ms": float(np.percentile(a, 95))}
