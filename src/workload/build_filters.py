"""Represent natural metadata predicates in an auditable form.

Predikat disimpan sebagai spesifikasi JSON (contoh: {"kabupaten": "Kabupaten Tanggamus",
"category": "alam"}) sehingga dapat ditinjau manusia dan dievaluasi ulang secara identik
oleh ground truth maupun seluruh metode pencarian.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

# Kolom korpus bertipe daftar: cocok bila nilai predikat ada di dalam daftar (berita ambigu: any_match)
LIST_COLUMNS = {"kabupaten", "province", "category", "entity_id"}


def equals(field: str, value):
    return lambda row: row.get(field) == value


def all_of(*predicates):
    return lambda row: all(p(row) for p in predicates)


# Identitas predikat yang stabil: JSON dengan kunci terurut
def spec_id(spec: dict) -> str:
    return json.dumps(spec, ensure_ascii=False, sort_keys=True)


# Mask boolean seluruh titik korpus yang memenuhi predikat (konjungsi seluruh kunci spesifikasi)
def filter_mask(corpus: pd.DataFrame, spec: dict) -> np.ndarray:
    mask = np.ones(len(corpus), dtype=bool)
    for key, value in spec.items():
        if key == "published_at_gte":
            mask &= (corpus["published_at"] >= pd.Timestamp(value)).fillna(False).to_numpy(dtype=bool)
        elif key in LIST_COLUMNS:
            mask &= corpus[key].apply(lambda daftar: value in daftar).to_numpy(dtype=bool)
        else:
            mask &= (corpus[key] == value).fillna(False).to_numpy(dtype=bool)
    return mask
