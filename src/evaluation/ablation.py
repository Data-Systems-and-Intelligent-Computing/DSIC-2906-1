"""Tabel ablasi AdaptiveL (README E5, bagian 40 item 12) dari log dev benchmark.

Satu baris per kombinasi L x n_sample x m_max, berisi recall@10 rata-rata per bin,
median perbandingan jarak, dan latensi p99. Memakai workload development, bukan workload test.

Jalankan dari root repo:
    python -m src.evaluation.ablation --dev-log results/raw/dev_benchmark_<...>.jsonl --out results/summary/ablation_<...>.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

# Parameter AdaptiveL yang divariasikan
PARAMS = ["L", "n_sample", "m_max"]


def ablation_table(dev_log: pd.DataFrame) -> pd.DataFrame:
    # Hanya baris AdaptiveL
    a = dev_log[dev_log["method"] == "adaptivel"].copy()
    for p in PARAMS:
        a[p] = a[p].astype(int)
    # Recall rata-rata per bin, satu kolom per bin (B2, B3, ...)
    recall = a.groupby(PARAMS + ["bin"])["recall_at_10"].mean().unstack("bin").add_prefix("recall_")
    # Biaya: median perbandingan jarak dan latensi p99 lintas semua kueri dev
    biaya = a.groupby(PARAMS).agg(dist_median=("distance_comparisons", "median"),
                                  lat_p99_ms=("latency_ms", lambda s: s.quantile(0.99)))
    return recall.join(biaya).round(3).reset_index()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev-log", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    t = ablation_table(pd.read_json(args.dev_log, lines=True))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(args.out, index=False)
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()