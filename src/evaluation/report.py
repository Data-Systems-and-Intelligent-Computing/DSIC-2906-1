"""Tabel hasil utama (README bagian 43) dari log benchmark utama.

Satu baris per (bin, tipe predikat, metode, konfigurasi), berisi recall@10 beserta CI 95%,
QPS, latensi p50/p95, persentase under-filled, median titik dikunjungi, dan median
evaluasi predikat. QPS dihitung dari latensi rata-rata karena kueri dijalankan
berurutan (implementasi Python).

Jalankan dari root repo:
    python -m src.evaluation.report --log results/raw/main_single_<...>.jsonl results/raw/main_compound_<...>.jsonl \
        [--stability results/summary/stability_<...>_per_pasangan.csv] --out-dir results/summary/main_<...>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.evaluation.bootstrap import mean_ci
from src.evaluation.latency import summarize_latency_ms

# Kolom pengelompokan tabel utama
GROUP_COLUMNS = ["bin", "type", "method", "config"]


def main_table(log: pd.DataFrame, extra_groups=()) -> pd.DataFrame:
    # Kolom pengelompokan: bin x tipe x metode x konfigurasi, ditambah pemecahan opsional
    cols = GROUP_COLUMNS + list(extra_groups)
    rows = []
    # dropna=False agar nilai kosong (mis. sumber kueri tak diketahui) tetap jadi kelompok sendiri
    for key, g in log.groupby(cols, dropna=False):
        row = dict(zip(cols, key))
        # Latensi persentil 50 dan 95 dari fungsi yang sudah ada
        lat = summarize_latency_ms(g["latency_ms"])
        # Interval kepercayaan 95% recall, dirata-ratakan per pasangan dulu agar ulangan tidak dihitung ganda
        per_pair = g.groupby("pair_id")["recall_at_10"].mean()
        _, (ci_low, ci_high) = mean_ci(per_pair)
        row.update({
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
        rows.append(row)
    return pd.DataFrame(rows)


# Gabungan semua tabel laporan; stabilitas digabung ke tabel utama bila tersedia
def build_report(log: pd.DataFrame, stability_per_pair: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    utama = main_table(log)
    if stability_per_pair is not None and len(stability_per_pair):
        # Rata-rata overlap@k per kelompok yang sama dengan tabel utama (README bagian 26)
        stab = (stability_per_pair.groupby(GROUP_COLUMNS)["overlap_at_k"].mean()
                .rename("stability_overlap").reset_index())
        utama = utama.merge(stab, on=GROUP_COLUMNS, how="left")
    return {
        "main_table": utama,
        "per_query_in_filter": main_table(log, extra_groups=["query_in_filter"]),
        "per_sumber_kueri": main_table(log, extra_groups=["query_source_type"]),
    }


# SHA-256 berkas sumber untuk metadata provenance
def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# Commit repo saat laporan dibuat
def _commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", nargs="+", required=True, help="satu atau lebih JSONL benchmark utama")
    ap.add_argument("--stability", default=None, help="CSV per pasangan dari src.benchmark.stability")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    # Log mentah dibaca tanpa diubah; beberapa berkas digabung
    log = pd.concat([pd.read_json(p, lines=True) for p in args.log], ignore_index=True)
    stab = pd.read_csv(args.stability) if args.stability else None
    tabel = build_report(log, stab)

    # Penulisan CSV dan metadata
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for nama, df in tabel.items():
        df.to_csv(out / f"{nama}.csv", index=False)
    meta = {
        "dibuat_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit_repo": _commit(),
        "sumber_log": {p: _sha256(p) for p in args.log},
        "sumber_stabilitas": {args.stability: _sha256(args.stability)} if args.stability else None,
        "n_baris_log": int(len(log)),
        "berkas_csv": sorted(f"{n}.csv" for n in tabel),
    }
    (out / "_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(tabel["main_table"].to_string(index=False))


if __name__ == "__main__":
    main()