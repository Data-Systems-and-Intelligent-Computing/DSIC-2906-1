"""Pelabelan kasus gagal per baris log benchmark utama (README E6, bagian 40 item 13).

Label kegagalan otomatis (satu baris log = satu pasangan x konfigurasi x ulangan), urutan prioritas:
- timeout: penelusuran dihentikan oleh batas waktu
- underfilled_topk: hasil kurang dari k
- low_recall: recall@10 di bawah ambang, padahal hasil penuh dan tanpa timeout
Label konteks (bukan kegagalan, untuk menjelaskan penyebab):
- highly_selective: match rate < 0,1 % (rezim B1)
- insufficient_eligible: pasangan set ekstensi (eligible < 10 x k)
- duplicate_dominance: sebagian besar hasil dari satu story_lineage atau vektor identik (butuh data korpus)
Kategori lain (predicate_mismatch, metadata_*, implementation_mismatch) diperiksa manual;
pelanggaran predikat sudah dihentikan langsung oleh runner.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FAILURE_CATEGORIES = [
    "underfilled_topk", "low_recall", "timeout", "predicate_mismatch",
    "metadata_missing", "metadata_incorrect", "duplicate_dominance", "implementation_mismatch"
]

# Ambang recall rendah untuk hasil yang penuh
LOW_RECALL_THRESHOLD = 0.5


# Satu label utama per baris: timeout > under-filled > recall rendah > ok
def primary_label(row) -> str:
    if bool(row["timeout"]):
        return "timeout"
    if bool(row["underfilled"]):
        return "underfilled_topk"
    if pd.notna(row["recall_at_10"]) and row["recall_at_10"] < LOW_RECALL_THRESHOLD:
        return "low_recall"
    return "ok"


# True bila lebih dari separuh hasil berasal dari satu kelompok (story_lineage atau vektor identik)
def _dominated(rows, lineage, dup_group, dominance: float) -> bool:
    rows = list(rows)
    if len(rows) < 2:
        return False
    for groups in (lineage, dup_group):
        if groups is None:
            continue
        keys = [str(groups[i]) for i in rows if groups[i] not in ("", None)]
        if keys:
            _, counts = np.unique(keys, return_counts=True)
            if counts.max() > 1 and counts.max() / len(rows) > dominance:
                return True
    return False


# Tambah kolom label kegagalan dan konteks ke log benchmark
def label_failures(log: pd.DataFrame, lineage=None, dup_group=None, dominance: float = 0.5) -> pd.DataFrame:
    out = log.copy()
    out["failure"] = out.apply(primary_label, axis=1)
    out["highly_selective"] = out["match_rate"] < 0.001
    out["insufficient_eligible"] = out["set"].eq("ekstensi") if "set" in out else False
    # Dominasi duplikat hanya bisa dihitung bila data korpus (lineage / grup vektor) diberikan
    if lineage is not None or dup_group is not None:
        out["duplicate_dominance"] = out["result_rows"].map(
            lambda r: _dominated(r, lineage, dup_group, dominance))
    return out


# Tabel failure taxonomy: persentase baris per label, per bin dan metode
def failure_taxonomy(labeled: pd.DataFrame) -> pd.DataFrame:
    t = labeled.groupby(["bin", "method", "failure"]).size().unstack("failure", fill_value=0)
    n = t.sum(axis=1)
    t = t.div(n, axis=0).mul(100).round(1)
    t.insert(0, "n_baris", n)
    return t.reset_index()