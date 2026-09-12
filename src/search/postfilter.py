"""Naive ANN + post-filter baseline utilities."""
from __future__ import annotations


def postfilter(candidate_ids, predicate, metadata_by_id, k: int = 10):
    out = []
    for idx in candidate_ids:
        if predicate(metadata_by_id[idx]):
            out.append(idx)
            if len(out) == k:
                break
    return out
