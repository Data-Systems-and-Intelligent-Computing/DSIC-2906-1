"""Append-only benchmark result logger."""
from __future__ import annotations
import json
from pathlib import Path


def append_jsonl(path: str, record: dict) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
