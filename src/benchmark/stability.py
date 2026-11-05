"""Stabilitas hasil kueri berulang (README bagian 26, RQ4/H4, E6).

overlap@k = |R1 ∩ R2| / k untuk dua hasil top-k dari kueri identik pada indeks, vektor,
metadata, predikat, dan profil sumber daya yang sama. Pembaginya k (bukan ukuran hasil),
sehingga hasil under-filled ikut menurunkan overlap.

Ringkasan dari log benchmark berulang:
    python -m src.benchmark.stability --log results/raw/stability_<...>.jsonl \
        --out results/summary/stability_<...>.csv
"""
from __future__ import annotations

import argparse
from itertools import combinations
from pathlib import Path

import pandas as pd


def overlap_at_k(a, b, k: int) -> float:
    """|R1 ∩ R2| / k, hanya memakai k hasil teratas masing-masing."""
    if k <= 0:
        raise ValueError("k harus positif")
    return len(set(list(a)[:k]) & set(list(b)[:k])) / k


# Dipertahankan untuk kompatibilitas; definisi resmi memakai overlap_at_k
def result_overlap(a, b) -> float:
    sa, sb = set(a), set(b)
    denom = max(len(sa), len(sb), 1)
    return len(sa & sb) / denom


# Overlap rata-rata seluruh pasangan ulangan untuk satu (pasangan kueri-filter, konfigurasi)
def pair_stability(results: list, k: int) -> float:
    pasangan = list(combinations(results, 2))
    if not pasangan:
        raise ValueError("butuh minimal dua ulangan")
    return sum(overlap_at_k(a, b, k) for a, b in pasangan) / len(pasangan)


def stability_table(log: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Kembalikan (stabilitas per pasangan x konfigurasi, ringkasan per bin x metode x konfigurasi)."""
    rows = []
    for (pair_id, config), g in log.groupby(["pair_id", "config"], sort=False):
        g = g.sort_values("repeat")
        rows.append({
            "pair_id": pair_id, "config": config, "method": g["method"].iloc[0], "bin": g["bin"].iloc[0],
            "type": g["type"].iloc[0], "n_repeat": len(g),
            "overlap_at_k": pair_stability(g["result_rows"].tolist(), int(g["k"].iloc[0])),
            "pct_timeout": float(g["timeout"].mean()),
        })
    per_pair = pd.DataFrame(rows)
    summary = (per_pair.groupby(["bin", "method", "config"])
               .agg(n_pasangan=("pair_id", "size"), overlap_mean=("overlap_at_k", "mean"),
                    overlap_min=("overlap_at_k", "min"), pct_overlap_lt_1=("overlap_at_k", lambda s: (s < 1).mean()),
                    pct_timeout=("pct_timeout", "mean"))
               .reset_index())
    return per_pair, summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    log = pd.read_json(args.log, lines=True)
    per_pair, summary = stability_table(log)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.out, index=False)
    per_pair.to_csv(str(args.out).replace(".csv", "_per_pasangan.csv"), index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
