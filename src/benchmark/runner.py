"""Benchmark runner contract: same queries, predicates, index, and resource profile."""
from __future__ import annotations

REQUIRED_LOG_FIELDS = [
    "query_id", "filter_id", "method", "resource_profile", "match_rate", "k",
    "latency_ms", "visited_nodes", "distance_comparisons", "predicate_evaluations",
    "returned_count", "timeout"
]
