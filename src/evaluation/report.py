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
from src.evaluation.failure_analysis import failure_taxonomy, label_failures
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
            # Biaya pencarian bebas bahasa pemrograman: median perhitungan jarak (D, Bab 2 subbab 2.10)
            "dist_comp_median": float(g["distance_comparisons"].median()),
        })
        rows.append(row)
    return pd.DataFrame(rows)


# Grafik item 6-7 README: recall dan biaya menurut match rate aktual, bukan menurut bin.
# Pasangan dikelompokkan ke n_groups kuantil match rate (dihitung per pasangan, bukan per baris log).
def per_match_rate(log: pd.DataFrame, n_groups: int = 8) -> pd.DataFrame:
    pasangan = log.drop_duplicates("pair_id")[["pair_id", "match_rate"]]
    # Jumlah kelompok tidak melebihi jumlah nilai match rate yang berbeda; satu nilai saja -> satu kelompok
    k = min(n_groups, pasangan["match_rate"].nunique())
    if k <= 1:
        kelompok = pd.Series(0, index=pasangan.index)
    else:
        kelompok = pd.qcut(pasangan["match_rate"], q=k, labels=False, duplicates="drop")
    peta = dict(zip(pasangan["pair_id"], kelompok))
    g = log.assign(mr_group=log["pair_id"].map(peta))
    out = (g.groupby(["mr_group", "method", "config"])
           .agg(n_pasangan=("pair_id", "nunique"), match_rate_median=("match_rate", "median"),
                recall_mean=("recall_at_10", "mean"), underfilled_pct=("underfilled", "mean"),
                visited_median=("visited_nodes", "median"), dist_comp_median=("distance_comparisons", "median"),
                pred_eval_median=("predicate_evaluations", "median"))
           .reset_index())
    out["underfilled_pct"] *= 100
    return out


# Gabungan semua tabel laporan; stabilitas digabung ke tabel utama bila tersedia
def build_report(log: pd.DataFrame, stability_per_pair: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    utama = main_table(log)
    if stability_per_pair is not None and len(stability_per_pair):
        # Rata-rata overlap@k per kelompok yang sama dengan tabel utama (README bagian 26)
        stab = (stability_per_pair.groupby(GROUP_COLUMNS)["overlap_at_k"].mean()
                .rename("stability_overlap").reset_index())
        utama = utama.merge(stab, on=GROUP_COLUMNS, how="left")
        # Proporsi pasangan dengan hasil identik di semua ulangan (bila kolomnya ada)
        if "identik" in stability_per_pair:
            iden = (stability_per_pair.groupby(GROUP_COLUMNS)["identik"].mean()
                    .rename("stability_identical").reset_index())
            utama = utama.merge(iden, on=GROUP_COLUMNS, how="left")
    return {
        "main_table": utama,
        "per_query_in_filter": main_table(log, extra_groups=["query_in_filter"]),
        "per_sumber_kueri": main_table(log, extra_groups=["query_source_type"]), 
        "failure_taxonomy": failure_taxonomy(label_failures(log)),
        "per_match_rate": per_match_rate(log),
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
    # DT-1: set utama dan set ekstensi dilaporkan terpisah
    ap.add_argument("--set", dest="set_name", choices=["utama", "ekstensi", "all"], default="all")
    args = ap.parse_args()

    # Log mentah dibaca tanpa diubah; beberapa berkas digabung
    log = pd.concat([pd.read_json(p, lines=True) for p in args.log], ignore_index=True)
    stab = pd.read_csv(args.stability) if args.stability else None
    # Penyaringan per set (DT-1); stabilitas ikut disaring lewat pair_id
    if args.set_name != "all":
        log = log[log["set"] == args.set_name].reset_index(drop=True)
        if stab is not None and "pair_id" in stab:
            stab = stab[stab["pair_id"].isin(log["pair_id"])].reset_index(drop=True)
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
        "set": args.set_name,
        "n_baris_log": int(len(log)),
        "berkas_csv": sorted(f"{n}.csv" for n in tabel),
    }
    (out / "_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(tabel["main_table"].to_string(index=False))


if __name__ == "__main__":
    main()