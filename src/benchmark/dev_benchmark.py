"""Development benchmark B0/B1/P1 untuk memilih parameter sebelum dibekukan (README bagian 21, 28 E5).

Kueri pengembangan = dokumen korpus acak (seed tetap), dengan dokumen kueri dikeluarkan
dari himpunan eligible agar tidak terjadi self-match. Ini BUKAN workload final: workload
final disusun dan dibekukan di Tahap 5, dan hasil dev tidak boleh dipakai sebagai hasil utama.

Jalankan dari root repo:  python -m src.benchmark.dev_benchmark
Output:  results/raw/dev_benchmark.jsonl  (satu baris per kueri x predikat x konfigurasi)
"""
from __future__ import annotations

import argparse
import itertools
import os
import time

import numpy as np
import pandas as pd

from src.groundtruth.exact_filtered_knn import exact_filtered_knn
from src.search.adaptivel import adaptivel_search
from src.search.graph_index import load_vamana_graph
from src.search.postfilter import postfilter_search
from src.search.twohop import twohop_search


# Predikat pengembangan: dua predikat layak (>= 100 titik) per bin B2-B5, dari tipe berbeda
def dev_predicates(corpus: pd.DataFrame) -> dict[str, np.ndarray]:
    has = lambda col, v: corpus[col].apply(lambda d: v in d).values
    preds = {
        "B5|kategori=alam": has("category", "alam"),
        "B5|temporal>=2026-07-23": (corpus["published_at"] >= "2026-07-23").values,
        "B4|penerbit=detik.com": (corpus["publisher_id"] == "detik.com").values,
        "B4|provinsi=Bali": has("province", "Bali"),
        "B3|penerbit=jawapos.com": (corpus["publisher_id"] == "jawapos.com").values,
        "B3|provinsi=Aceh": has("province", "Aceh"),
        "B2|kabupaten=Tanggamus": has("kabupaten", "Kabupaten Tanggamus"),
        "B2|kabupaten=Pangandaran∧alam": has("kabupaten", "Kabupaten Pangandaran") & has("category", "alam"),
    }
    return preds


# Konfigurasi: setiap metode pada L_search 100/200/400 (kurva recall-biaya, README A1);
# P1 dengan n_sample 32/64 (harus lebih kecil dari jumlah titik yang dikunjungi, kira-kira L) dan m_max 1/2/4/8
def configs() -> list[dict]:
    out = [{"method": "postfilter", "candidate_budget": L} for L in (100, 200, 400)]
    out += [{"method": "twohop", "L": L} for L in (100, 200, 400)]
    for L in (100, 200, 400):
        out.append({"method": "adaptivel", "L": L, "n_sample": 64, "m_max": 1})
        out += [{"method": "adaptivel", "L": L, "n_sample": n, "m_max": m}
                for m, n in itertools.product((2, 4, 8), (32, 64))]
    return out


def run_one(cfg: dict, q, vectors, neighbors, start, eligible, k):
    if cfg["method"] == "postfilter":
        return postfilter_search(q, vectors, neighbors, start, eligible, k, cfg["candidate_budget"])
    if cfg["method"] == "twohop":
        return twohop_search(q, vectors, neighbors, start, eligible, k, cfg["L"])
    return adaptivel_search(q, vectors, neighbors, start, eligible, k, cfg["L"], cfg["n_sample"], cfg["m_max"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-queries", type=int, default=100)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--seed", type=int, default=2906)
    ap.add_argument("--out", default="results/raw/dev_benchmark.jsonl")
    args = ap.parse_args()

    vectors = np.load("data/embeddings/base_vectors.npy")
    start, neighbors = load_vamana_graph("index/diskann/tourism")
    corpus = pd.read_parquet("data/processed/corpus.parquet")
    preds = dev_predicates(corpus)
    query_idx = np.random.default_rng(args.seed).choice(len(vectors), size=args.n_queries, replace=False)

    rows = []
    for filter_id, mask in preds.items():
        match_rate = float(mask.mean())
        for qi in query_idx:
            # Himpunan eligible tanpa dokumen kueri, dan ground truth eksaknya
            eligible = mask.copy()
            eligible[qi] = False
            if eligible.sum() < args.k:
                continue
            gt = set(exact_filtered_knn(vectors, vectors[qi], eligible, k=args.k).tolist())

            for cfg in configs():
                t0 = time.perf_counter()
                result, stats = run_one(cfg, vectors[qi], vectors, neighbors, start, eligible, args.k)
                latency_ms = (time.perf_counter() - t0) * 1000
                if not all(eligible[i] for i in result):
                    raise AssertionError(f"Hasil melanggar predikat: {cfg} {filter_id} kueri {qi}")
                rows.append({
                    "query_id": int(qi), "filter_id": filter_id, "bin": filter_id.split("|")[0],
                    "match_rate": match_rate, "k": args.k, "resource_profile": "dev-local",
                    "config": " ".join(f"{a}={b}" for a, b in cfg.items()),
                    "recall_at_10": len(gt & set(result)) / args.k,
                    "latency_ms": latency_ms, "timeout": False, **stats,
                })
        print(f"selesai: {filter_id} (match rate {match_rate * 100:.3f}%)")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    pd.DataFrame(rows).to_json(args.out, orient="records", lines=True)
    print(f"{len(rows)} baris -> {args.out}")


if __name__ == "__main__":
    main()
