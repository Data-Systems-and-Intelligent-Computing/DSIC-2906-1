"""Benchmark runner contract: same queries, predicates, index, and resource profile."""
from __future__ import annotations

REQUIRED_LOG_FIELDS = [
    "query_id", "filter_id", "method", "resource_profile", "match_rate", "k",
    "latency_ms", "visited_nodes", "distance_comparisons", "predicate_evaluations",
    "returned_count", "timeout",
    # Ditambahkan untuk Minggu 2 (P3, P4): bernilai null untuk metode yang tidak memakainya
    "sp_hat", "multiplier", "n_match_sample", "predicate_evaluations_unique",
]
