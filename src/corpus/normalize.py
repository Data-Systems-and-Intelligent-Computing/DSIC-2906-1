"""Corpus normalization for heterogeneous tourism records."""
from __future__ import annotations

import pandas as pd


def normalize_text_frame(df: pd.DataFrame, text_column: str = "text") -> pd.DataFrame:
    out = df.copy()
    out[text_column] = out[text_column].fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    return out
