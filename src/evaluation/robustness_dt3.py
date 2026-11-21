"""Robustness check DT-3 opsi C: predikat wilayah/kategori hanya untuk dokumen bernilai tunggal.

Dasar: draf pembimbing (draft-teori-dasar-feby.md) bagian 7 DT-3 dan bagian 8 P7. Benchmark utama memakai
any-match (opsi A): dokumen dengan beberapa kabupaten, provinsi, atau kategori lolos filter bila salah satu
nilainya cocok. Robustness (opsi B) mengulang setiap pasangan yang predikatnya memuat kabupaten, provinsi,
atau kategori, dengan dokumen yang punya lebih dari satu nilai pada kolom predikat itu dikeluarkan dari
himpunan eligible; ground truth eksak dihitung ulang dan ketiga metode dijalankan dengan parameter beku
yang sama. Hasil utama tidak diubah; keluaran ditulis ke berkas terpisah.

Yang dilaporkan hanya recall, under-fill, dan biaya D/E (tidak bergantung pada mesin), sehingga
analisis ini sah dijalankan di luar mesin benchmark resmi. Latensi tidak dipakai.

Jalankan dari root repo:
    python -m src.evaluation.robustness_dt3 --main-log results/raw/main_single_<...>.jsonl results/raw/main_compound_<...>.jsonl \
        --out-log results/raw/robustness_dt3_<tanggal>.jsonl --out-dir results/summary/robustness_dt3_<tanggal>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.benchmark.logger import append_jsonl
from src.benchmark.main_benchmark import check_frozen, method_configs, run_one
from src.evaluation.bootstrap import paired_mean_diff_ci
from src.evaluation.report import paired_comparisons
from src.groundtruth.build_groundtruth import eligible_for_pair
from src.groundtruth.exact_filtered_knn import exact_filtered_knn
from src.workload.build_filters import filter_mask

# Kolom bernilai daftar yang terkena aturan any-match (DT-3: wilayah dan kategori)
AMBIGUOUS_KEYS = ("kabupaten", "province", "category")


# Penanda dokumen bernilai ganda per kolom: True bila daftar pada kolom itu berisi lebih dari satu nilai
def multi_valued(corpus: pd.DataFrame) -> dict[str, np.ndarray]:
    return {k: corpus[k].apply(lambda d: d is not None and len(d) > 1).to_numpy(dtype=bool)
            for k in AMBIGUOUS_KEYS if k in corpus}


# Mask opsi B: predikat seperti biasa, lalu dokumen bernilai ganda pada kolom predikat dikeluarkan.
# Predikat yang tidak memuat kolom wilayah/kategori tidak termasuk analisis ini (None).
def robust_mask(corpus: pd.DataFrame, spec: dict, multi: dict[str, np.ndarray]) -> np.ndarray | None:
    kunci = [k for k in spec if k in multi]
    if not kunci:
        return None
    mask = filter_mask(corpus, spec)
    for k in kunci:
        mask &= ~multi[k]
    return mask


def run_robustness(corpus, vectors, neighbors, start, workload, configs, k, timeout_ms, sink=None) -> list[dict]:
    multi = multi_valued(corpus)
    masks: dict[str, np.ndarray | None] = {}
    out = []
    for pr in workload.itertuples(index=False):
        if pr.filter_id not in masks:
            masks[pr.filter_id] = robust_mask(corpus, json.loads(pr.filter_id), multi)
        mask = masks[pr.filter_id]
        if mask is None:
            continue
        eligible = eligible_for_pair(mask, pr.excluded_rows)
        n_el = int(eligible.sum())
        base = {"pair_id": pr.pair_id, "set": pr.set, "bin": pr.bin, "type": pr.type, "filter_id": pr.filter_id,
                "n_eligible_main": int(pr.n_eligible), "n_eligible_robust": n_el, "k": k}
        # Pasangan yang tidak lagi punya k dokumen eligible dicatat dan dilewati (recall tidak terdefinisi)
        if n_el < k:
            rec = {**base, "skipped": True}
            out.append(rec)
            if sink:
                sink(rec)
            continue
        q = vectors[pr.query_row]
        # Ground truth eksak dihitung ulang untuk himpunan eligible tanpa berita ambigu
        truth = set(int(i) for i in exact_filtered_knn(vectors, q, eligible, k=k))
        for c in configs:
            result, stats = run_one(c, q, vectors, neighbors, start, eligible, k, timeout_ms)
            if not all(eligible[i] for i in result):
                raise AssertionError(f"Hasil melanggar predikat: {c} {pr.pair_id}")
            rec = {**base, "skipped": False, "method": c["method"],
                   "config": " ".join(f"{a}={b}" for a, b in c.items()),
                   "recall_at_10": len(truth & set(result)) / k, "underfilled": len(result) < k,
                   "visited_nodes": stats["visited_nodes"], "distance_comparisons": stats["distance_comparisons"],
                   "predicate_evaluations": stats["predicate_evaluations"], "timeout": bool(stats.get("timeout"))}
            out.append(rec)
            if sink:
                sink(rec)
    return out


# Perbandingan dengan hasil utama pada pasangan dan konfigurasi yang sama
def compare_with_main(robust: pd.DataFrame, main: pd.DataFrame) -> dict[str, pd.DataFrame]:
    r = robust[~robust["skipped"]]
    m = main.groupby(["pair_id", "config"], as_index=False)[["recall_at_10", "underfilled"]].mean()
    j = r.merge(m, on=["pair_id", "config"], suffixes=("_robust", "_main"))
    rows = []
    for (s, b, meth, cfg), g in j.groupby(["set", "bin", "method", "config"]):
        diff, (lo, hi) = paired_mean_diff_ci(g["recall_at_10_robust"].to_numpy(), g["recall_at_10_main"].to_numpy())
        rows.append({"set": s, "bin": b, "method": meth, "config": cfg, "n_pasangan": int(len(g)),
                     "recall_main": float(g["recall_at_10_main"].mean()),
                     "recall_robust": float(g["recall_at_10_robust"].mean()),
                     "selisih_robust_minus_main": diff, "ci_low": lo, "ci_high": hi,
                     "underfilled_main_pct": float(g["underfilled_main"].mean() * 100),
                     "underfilled_robust_pct": float(g["underfilled_robust"].mean() * 100)})
    per_set = {}
    # Perbandingan antarmetode dalam kondisi robust, dengan pembanding yang sama seperti laporan utama
    for s, g in r.groupby("set"):
        per_set[f"paired_comparisons_robust_{s}"] = paired_comparisons(g)
    cakupan = (robust.drop_duplicates("pair_id").groupby(["set", "bin"])
               .agg(n_pasangan_wilayah=("pair_id", "size"), n_dilewati=("skipped", "sum"),
                    eligible_main_median=("n_eligible_main", "median"),
                    eligible_robust_median=("n_eligible_robust", "median")).reset_index())
    return {"robust_vs_main": pd.DataFrame(rows), "cakupan": cakupan, **per_set}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--main-log", nargs="+", required=True, help="JSONL benchmark utama (single + compound)")
    ap.add_argument("--out-log", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--config", default="configs/main_benchmark.yaml")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    check_frozen(cfg)
    from src.search.graph_index import load_vamana_graph
    corpus = pd.read_parquet("data/processed/corpus.parquet")
    vectors = np.load("data/embeddings/base_vectors.npy")
    start, neighbors = load_vamana_graph("index/diskann/tourism")
    workload = pd.read_parquet("data/processed/workload.parquet")

    # Log lama untuk nama berkas yang sama dihapus dulu agar tidak tergabung dua kali
    Path(args.out_log).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_log).write_text("", encoding="utf-8")
    recs = run_robustness(corpus, vectors, neighbors, start, workload, method_configs(cfg), int(cfg["k"]),
                          cfg.get("timeout_ms"), sink=lambda r: append_jsonl(args.out_log, r))

    main_log = pd.concat([pd.read_json(p, lines=True) for p in args.main_log], ignore_index=True)
    tabel = compare_with_main(pd.DataFrame(recs), main_log)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for nama, df in tabel.items():
        df.to_csv(out / f"{nama}.csv", index=False)
    (out / "_meta.json").write_text(json.dumps({"params_frozen_at": cfg.get("frozen_at"),
                                                "sumber_log_utama": args.main_log, "log_robust": args.out_log,
                                                "aturan": "DT-3 opsi B: dokumen bernilai ganda pada kolom predikat (kabupaten/provinsi/kategori) dikeluarkan"},
                                               ensure_ascii=False, indent=2), encoding="utf-8")
    print(tabel["cakupan"].to_string(index=False))


if __name__ == "__main__":
    main()
