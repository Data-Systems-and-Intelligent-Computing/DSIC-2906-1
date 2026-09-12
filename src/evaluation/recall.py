"""Filtered Recall@k."""
from __future__ import annotations


def recall_at_k(found, ground_truth, k: int = 10) -> float:
    gt = list(ground_truth)[:k]
    if not gt:
        raise ValueError("ground truth must be non-empty")
    return len(set(found[:k]) & set(gt)) / len(gt)
