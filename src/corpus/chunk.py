"""Deterministic character-based chunking used only when documents require it."""
from __future__ import annotations


def chunk_text(text: str, max_chars: int = 1800, overlap_chars: int = 200) -> list[str]:
    if max_chars <= 0 or overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("Require max_chars > overlap_chars >= 0")
    if len(text) <= max_chars:
        return [text]
    step = max_chars - overlap_chars
    return [text[i:i + max_chars] for i in range(0, len(text), step) if text[i:i + max_chars]]
