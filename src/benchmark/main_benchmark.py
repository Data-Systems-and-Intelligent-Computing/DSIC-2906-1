"""Benchmark utama Minggu 3: predikat tunggal dan majemuk pada workload beku (scripts 09-11).

Menjalankan PostFilter, TwoHop, dan AdaptiveL dengan parameter beku dari
configs/main_benchmark.yaml pada pasangan kueri-filter workload beku, lalu menghitung
recall@k terhadap ground truth eksak. Himpunan eligible setiap pasangan dibentuk ulang
dengan aturan yang sama dengan ground truth (filter_mask dikurangi excluded_rows), dan
jumlahnya dicocokkan dengan workload.

Pengaman: runner menolak berjalan selama configs/main_benchmark.yaml belum frozen: true,
agar hasil workload test tidak terlihat sebelum parameter dibekukan.

Jalankan dari root repo:
    python -m src.benchmark.main_benchmark --types single --resource-profile lightsail-t3.xlarge \
        --out results/raw/main_single_<tanggal>.jsonl
Output: JSONL satu baris per pasangan x konfigurasi, dengan seluruh REQUIRED_LOG_FIELDS.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.benchmark.dev_benchmark import git_commit
from src.benchmark.logger import append_jsonl
from src.benchmark.runner import REQUIRED_LOG_FIELDS
from src.groundtruth.build_groundtruth import eligible_for_pair
from src.search.adaptivel import adaptivel_search
from src.search.graph_index import load_vamana_graph
from src.search.postfilter import postfilter_search
from src.search.twohop import twohop_search
from src.workload.build_filters import filter_mask


# Daftar konfigurasi metode dari berkas parameter beku (produk kartesius nilai L/budget)
def method_configs(cfg: dict) -> list[dict]:
    m = cfg["methods"]
    out = [{"method": "postfilter", "candidate_budget": b} for b in m["postfilter"]["candidate_budget"]]
    out += [{"method": "twohop", "L": L} for L in m["twohop"]["L"]]
    a = m["adaptivel"]
    out += [{"method": "adaptivel", "L": L, "n_sample": a["n_sample"], "m_max": a["m_max"]} for L in a["L"]]
    return out


# Parameter wajib terisi dan berkas ditandai beku sebelum workload test dijalankan
def check_frozen(cfg: dict) -> None:
    if cfg.get("frozen") is not True:
        raise SystemExit("configs/main_benchmark.yaml belum frozen: true; benchmark utama tidak dijalankan")
    for c in method_configs(cfg):
        kosong = [k for k, v in c.items() if v is None]
        if kosong:
            raise SystemExit(f"parameter belum diisi untuk {c['method']}: {kosong}")


# Satu pencarian dengan timeout yang sama untuk semua metode
def run_one(c: dict, q, vectors, neighbors, start, eligible, k: int, timeout_ms):
    if c["method"] == "postfilter":
        return postfilter_search(q, vectors, neighbors, start, eligible, k, c["candidate_budget"], timeout_ms=timeout_ms)
    if c["method"] == "twohop":
        return twohop_search(q, vectors, neighbors, start, eligible, k, c["L"], timeout_ms=timeout_ms)
    return adaptivel_search(q, vectors, neighbors, start, eligible, k, c["L"], c["n_sample"], c["m_max"],
                            timeout_ms=timeout_ms)


# Inti benchmark tanpa I/O berkas, agar bisa diuji dengan data sintetis
def run_pairs(corpus: pd.DataFrame, vectors: np.ndarray, neighbors, start: int, workload: pd.DataFrame,
              gt: pd.DataFrame, configs: list[dict], k: int, timeout_ms, meta: dict, sink=None,
              repeats: int = 1) -> list[dict]:
    gt_rows = dict(zip(gt["pair_id"], gt["gt_rows"]))
    masks: dict[str, np.ndarray] = {}
    out = []
    for pr in workload.itertuples(index=False):
        if pr.filter_id not in masks:
            masks[pr.filter_id] = filter_mask(corpus, json.loads(pr.filter_id))
        eligible = eligible_for_pair(masks[pr.filter_id], pr.excluded_rows)
        if int(eligible.sum()) != pr.n_eligible:
            raise AssertionError(f"Jumlah eligible {pr.pair_id} tidak sama dengan workload")
        truth = set(int(i) for i in gt_rows[pr.pair_id][:k])
        q = vectors[pr.query_row]

        batch = []
        # Ulangan kueri identik untuk stabilitas (README bagian 26); repeats=1 untuk benchmark biasa
        for c, rep_i in itertools.product(configs, range(repeats)):
            t0 = time.perf_counter()
            result, stats = run_one(c, q, vectors, neighbors, start, eligible, k, timeout_ms)
            latency_ms = (time.perf_counter() - t0) * 1000
            if not all(eligible[i] for i in result):
                raise AssertionError(f"Hasil melanggar predikat: {c} {pr.pair_id}")
            rec = {f: None for f in REQUIRED_LOG_FIELDS}
            rec.update(stats)
            rec.update({
                "pair_id": pr.pair_id, "query_id": f"Q{pr.query_row:05d}", "query_row": int(pr.query_row),
                "filter_id": pr.filter_id, "set": pr.set, "bin": pr.bin, "type": pr.type,
                "match_rate": float(pr.match_rate), "n_eligible": int(pr.n_eligible), "k": k,
                "config": " ".join(f"{a}={b}" for a, b in c.items()),
                "recall_at_10": len(truth & set(result)) / len(truth) if truth else None,
                "latency_ms": latency_ms, "timeout_ms": timeout_ms, "repeat": rep_i,
                "result_rows": [int(i) for i in result],
                "timeout": bool(stats.get("timeout", False)),
                **meta,
            })
            hilang = [f for f in REQUIRED_LOG_FIELDS if f not in rec]
            if hilang:
                raise AssertionError(f"Field log wajib hilang: {hilang}")
            batch.append(rec)
        out.extend(batch)
        if sink is not None:
            for rec in batch:
                sink(rec)
    return out


# SHA-256 berkas untuk dicatat di setiap baris log
def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/main_benchmark.yaml")
    ap.add_argument("--types", choices=["single", "compound", "all"], default="single")
    ap.add_argument("--set", dest="set_name", choices=["utama", "ekstensi", "all"], default="all")
    ap.add_argument("--resource-profile", required=True, help="mis. lightsail-t3.xlarge")
    ap.add_argument("--out", required=True)
    ap.add_argument("--repeats", type=int, default=1, help="ulangan kueri identik untuk stabilitas (E6)")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    check_frozen(cfg)
    wcfg = yaml.safe_load(Path("configs/workload.yaml").read_text(encoding="utf-8"))
    k, timeout_ms = int(cfg["k"]), cfg.get("timeout_ms")

    # Artefak beku
    corpus = pd.read_parquet("data/processed/corpus.parquet")
    vectors = np.load("data/embeddings/base_vectors.npy")
    start, neighbors = load_vamana_graph("index/diskann/tourism")
    workload = pd.read_parquet("data/processed/workload.parquet")
    gt = pd.read_parquet("data/groundtruth/filtered_knn_k10.parquet")
    wman = pd.read_csv("data/manifests/workload_manifest.csv").iloc[0]
    if sha256("data/processed/workload.parquet") != wman["checksum_sha256"]:
        raise SystemExit("workload.parquet tidak sama dengan manifest; benchmark dihentikan")

    # Pemilihan pasangan menurut tipe predikat dan set
    tipe = wcfg["predicate_types"]
    allowed = tipe["single"] if args.types == "single" else tipe["compound"] if args.types == "compound" \
        else tipe["single"] + tipe["compound"]
    sel = workload[workload["type"].isin(allowed)]
    if args.set_name != "all":
        sel = sel[sel["set"] == args.set_name]

    meta = {
        "resource_profile": args.resource_profile, "commit": git_commit(),
        "workload_id": wman["workload_id"], "workload_sha256": wman["checksum_sha256"],
        "groundtruth_sha256": sha256("data/groundtruth/filtered_knn_k10.parquet"),
        "params_frozen_at": cfg.get("frozen_at"), "threads": cfg.get("threads"),
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
        "run_started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    configs = method_configs(cfg)
    print(f"{len(sel)} pasangan x {len(configs)} konfigurasi x {args.repeats} ulangan -> {args.out}")
    run_pairs(corpus, vectors, neighbors, start, sel, gt, configs, k, timeout_ms, meta,
              sink=lambda r: append_jsonl(args.out, r), repeats=args.repeats)
    print("selesai")


if __name__ == "__main__":
    main()
