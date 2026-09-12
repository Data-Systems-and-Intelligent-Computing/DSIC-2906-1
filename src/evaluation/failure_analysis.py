"""Failure labels for under-filled, low-recall, timeout, and metadata-quality cases."""
FAILURE_CATEGORIES = [
    "underfilled_topk", "low_recall", "timeout", "predicate_mismatch",
    "metadata_missing", "metadata_incorrect", "duplicate_dominance", "implementation_mismatch"
]
