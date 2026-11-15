"""Benchmark paralel: throughput per profil core (draf P5) dan stabilitas konkuren dengan timeout (DT-7).

Mode throughput: untuk setiap konfigurasi metode, seluruh pasangan dibagi ke W proses yang berjalan
bersamaan; QPS = jumlah pasangan / waktu dinding. Recall dicatat untuk memastikan hasil sama dengan
benchmark utama (paralelisme tidak boleh mengubah hasil bila tidak ada timeout).

Mode stability: setiap pasangan x konfigurasi dikirim dua kali berturut-turut ke kumpulan W proses,
sehingga kedua salinan berjalan bersamaan di proses berbeda (cara pengukuran paper bagian 3.2).
Ketidakstabilan hanya dapat muncul dari timeout yang dipicu perebutan CPU; overlap@k dan proporsi
hasil identik dihitung per salinan.

Parameter dibaca dari configs/main_benchmark.yaml (beku) dan configs/parallel_benchmark.yaml (beku).

Jalankan dari root repo (lihat scripts/15_parallel_throughput.sh dan 16_concurrent_stability.sh):
    python -m src.benchmark.parallel_benchmark --mode throughput --workers 4 --profile RC-reference --out <jsonl>
    python -m src.benchmark.parallel_benchmark --mode stability --workers 4 --timeout-ms 45 --out <jsonl>
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.benchmark.logger import append_jsonl
from src.benchmark.main_benchmark import check_frozen, method_configs, run_one
from src.workload.build_filters import filter_mask

# Data bersama untuk proses pekerja; diisi sebelum fork sehingga tidak disalin ulang per tugas
_D: dict = {}


def _siapkan(corpus, vectors, neighbors, start, workload, gt, k):
    masks = {f: filter_mask(corpus, json.loads(f)) for f in workload["filter_id"].unique()}
    _D.update(vectors=vectors, neighbors=neighbors, start=start, k=k, masks=masks,
              pairs=workload.reset_index(drop=True),
              truth=dict(zip(gt["pair_id"], [set(int(i) for i in r[:k]) for r in gt["gt_rows"]])))


# Satu pencarian: indeks pasangan, konfigurasi, timeout -> hasil dan statistik ringkas
def _cari(tugas):
    i, c, timeout_ms = tugas
    pr = _D["pairs"].iloc[i]
    eligible = _D["masks"][pr["filter_id"]].copy()
    eligible[np.asarray(pr["excluded_rows"], dtype=np.int64)] = False
    t0 = time.perf_counter()
    result, stats = run_one(c, _D["vectors"][int(pr["query_row"])], _D["vectors"], _D["neighbors"], _D["start"],
                            eligible, _D["k"], timeout_ms)
    lat = (time.perf_counter() - t0) * 1000
    truth = _D["truth"][pr["pair_id"]]
    return {"pair_id": pr["pair_id"], "set": pr["set"], "bin": pr["bin"], "type": pr["type"],
            "method": c["method"], "config": " ".join(f"{a}={b}" for a, b in c.items()),
            "recall_at_10": len(truth & set(result)) / len(truth), "result_rows": [int(x) for x in result],
            "underfilled": len(result) < _D["k"], "timeout": bool(stats.get("timeout")), "latency_ms": lat}


def _pool(workers: int):
    # fork: data bersama diwarisi pekerja tanpa disalin (Linux); satu pekerja dijalankan tanpa pool
    return mp.get_context("fork").Pool(workers) if workers > 1 else None


def run_throughput(configs, workers: int, timeout_ms, sink=None) -> list[dict]:
    n = len(_D["pairs"])
    ringkas = []
    pool = _pool(workers)
    try:
        for c in configs:
            tugas = [(i, c, timeout_ms) for i in range(n)]
            t0 = time.perf_counter()
            hasil = pool.map(_cari, tugas, chunksize=8) if pool else [_cari(t) for t in tugas]
            dinding = time.perf_counter() - t0
            for r in hasil:
                r.update(workers=workers, wall_s_config=dinding)
                if sink:
                    sink(r)
            ringkas.append({"config": hasil[0]["config"], "method": c["method"], "workers": workers,
                            "n_kueri": n, "wall_s": dinding, "qps": n / dinding,
                            "recall_mean": float(np.mean([r["recall_at_10"] for r in hasil])),
                            "timeout_pct": 100 * float(np.mean([r["timeout"] for r in hasil]))})
    finally:
        if pool:
            pool.close(); pool.join()
    return ringkas


def run_stability(configs, workers: int, copies: int, timeout_ms, sink=None) -> list[dict]:
    n = len(_D["pairs"])
    # Salinan identik berurutan dalam antrean dengan chunksize 1, sehingga diambil proses berbeda secara bersamaan
    tugas = [(i, c, timeout_ms) for i in range(n) for c in configs for _ in range(copies)]
    pool = _pool(workers)
    try:
        hasil = list(pool.imap(_cari, tugas, chunksize=1)) if pool else [_cari(t) for t in tugas]
    finally:
        if pool:
            pool.close(); pool.join()
    for j, r in enumerate(hasil):
        r.update(copy=j % copies, workers=workers, timeout_ms=timeout_ms)
        if sink:
            sink(r)
    return hasil


# Ringkasan stabilitas konkuren per bin x metode x konfigurasi
def stability_summary(log: pd.DataFrame, k: int = 10) -> pd.DataFrame:
    rows = []
    for (pid, cfg), g in log.groupby(["pair_id", "config"], sort=False):
        res = [list(x)[:k] for x in g["result_rows"]]
        a, b = set(res[0]), set(res[1])
        rows.append({"pair_id": pid, "config": cfg, "set": g["set"].iloc[0], "bin": g["bin"].iloc[0],
                     "method": g["method"].iloc[0], "overlap_at_k": len(a & b) / k,
                     "identik": res[0] == res[1], "ada_timeout": bool(g["timeout"].any())})
    t = pd.DataFrame(rows)
    out = (t.groupby(["set", "bin", "method", "config"])
           .agg(n_pasangan=("pair_id", "size"), overlap_mean=("overlap_at_k", "mean"),
                identik_pct=("identik", "mean"), timeout_pct=("ada_timeout", "mean")).reset_index())
    out[["identik_pct", "timeout_pct"]] *= 100
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["throughput", "stability"], required=True)
    ap.add_argument("--workers", type=int, required=True)
    ap.add_argument("--profile", default=None, help="nama profil untuk mode throughput")
    ap.add_argument("--timeout-ms", type=float, default=None, help="timeout mode stability")
    ap.add_argument("--out", required=True, help="JSONL per pencarian")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path("configs/main_benchmark.yaml").read_text(encoding="utf-8"))
    pcfg = yaml.safe_load(Path("configs/parallel_benchmark.yaml").read_text(encoding="utf-8"))
    check_frozen(cfg)
    # Config paralel tidak berisi grid metode, jadi cukup diperiksa penanda bekunya
    if pcfg.get("frozen") is not True:
        raise SystemExit("configs/parallel_benchmark.yaml belum frozen: true; benchmark paralel tidak dijalankan")
    from src.search.graph_index import load_vamana_graph
    corpus = pd.read_parquet("data/processed/corpus.parquet")
    vectors = np.load("data/embeddings/base_vectors.npy")
    start, neighbors = load_vamana_graph("index/diskann/tourism")
    workload = pd.read_parquet("data/processed/workload.parquet")
    gt = pd.read_parquet("data/groundtruth/filtered_knn_k10.parquet")
    _siapkan(corpus, vectors, neighbors, start, workload, gt, int(cfg["k"]))

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("", encoding="utf-8")
    sink = lambda r: append_jsonl(args.out, r)  # noqa: E731
    configs = method_configs(cfg)
    if args.mode == "throughput":
        ringkas = pd.DataFrame(run_throughput(configs, args.workers, pcfg["throughput"]["timeout_ms"], sink))
        ringkas.insert(0, "profile", args.profile)
        ringkas.to_csv(str(args.out).replace(".jsonl", "_ringkas.csv"), index=False)
        print(ringkas.round(3).to_string(index=False))
    else:
        log = pd.DataFrame(run_stability(configs, args.workers, int(pcfg["stability"]["copies"]), args.timeout_ms, sink))
        ringkas = stability_summary(log, int(cfg["k"]))
        ringkas.to_csv(str(args.out).replace(".jsonl", "_ringkas.csv"), index=False)
        print(ringkas.groupby("method")[["overlap_mean", "identik_pct", "timeout_pct"]].mean().round(3))


if __name__ == "__main__":
    main()
