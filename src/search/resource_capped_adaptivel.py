"""Optional engineering adaptation: AdaptiveL with explicit resource guards."""
from __future__ import annotations


def validate_resource_guards(max_visited_nodes=None, max_distance_comparisons=None, query_timeout_ms=None):
    values = [max_visited_nodes, max_distance_comparisons, query_timeout_ms]
    if all(v is None for v in values):
        raise ValueError("At least one explicit resource guard is required for RC-AdaptiveL")
    if any(v is not None and v <= 0 for v in values):
        raise ValueError("Resource guards must be positive")
