"""Natural metadata extraction and validation."""
from __future__ import annotations

REQUIRED_POINT_FIELDS = {
    "doc_id", "chunk_id", "text", "source_type", "source_id", "fetched_at", "snapshot_id"
}


def validate_point_metadata(record: dict) -> None:
    missing = REQUIRED_POINT_FIELDS.difference(record)
    if missing:
        raise ValueError(f"Missing required point fields: {sorted(missing)}")
