"""Tabel hasil utama (README bagian 43) dari log benchmark utama.

Satu baris per (bin, tipe predikat, metode, konfigurasi), berisi recall@10, QPS,
latensi p50/p95, persentase under-filled, median titik dikunjungi, dan median
evaluasi predikat. QPS dihitung dari latensi rata-rata karena kueri dijalankan
berurutan (implementasi Python).
"""
from __future__ import annotations

import pandas as pd

from src.evaluation.latency import summarize_latency_ms
from src.evaluation.bootstrap import mean_ci

# Kolom pengelompokan tabel utama
GROUP_COLUMNS = ["bin", "type", "method", "config"]


def main_table(log: pd.DataFrame) -> pd.DataFrame:
    rows = []
    # Satu kelompok = satu kombinasi bin x tipe predikat x metode x konfigurasi
    for (b, t, m, c), g in log.groupby(GROUP_COLUMNS):
        # Latensi persentil 50 dan 95 dari fungsi yang sudah ada
        lat = summarize_latency_ms(g["latency_ms"])
        # Interval kepercayaan 95% recall, dirata-ratakan per pasangan dulu agar ulangan tidak dihitung ganda
        per_pair = g.groupby("pair_id")["recall_at_10"].mean()
        _, (ci_low, ci_high) = mean_ci(per_pair)
        rows.append({
            "bin": b,
            "type": t,
            "method": m,
            "config": c,
            # Banyaknya pasangan kueri-filter di kelompok ini
            "n_pasangan": int(g["pair_id"].nunique()),
            # Akurasi: rata-rata recall@10 terhadap ground truth eksak
            "recall_mean": float(g["recall_at_10"].mean()),
            "recall_ci_low": ci_low,
            "recall_ci_high": ci_high,
            # Throughput: kueri per detik dari latensi rata-rata (ms)
            "qps": float(1000 / g["latency_ms"].mean()),
            "p50_ms": lat["p50_ms"],
            "p95_ms": lat["p95_ms"],
            # Persentase hasil yang kurang dari k
            "underfilled_pct": float(g["underfilled"].mean() * 100),
            # Biaya pencarian: median titik dikunjungi dan evaluasi predikat
            "visited_median": float(g["visited_nodes"].median()),
            "pred_eval_median": float(g["predicate_evaluations"].median()),
        })
    return pd.DataFrame(rows)
