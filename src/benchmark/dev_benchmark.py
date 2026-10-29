"""Development benchmark B0/B1/P1 untuk memilih parameter sebelum dibekukan (README bagian 21, 28 E5).

Kueri pengembangan = dokumen korpus acak (seed tetap; sama dengan dev_queries di
configs/workload.yaml sehingga tidak dipakai lagi sebagai kueri test). Aturan self-match
sama dengan workload beku (src.workload.build_queries.excluded_rows): dokumen kueri,
dokumen bervektor identik, dan dokumen satu story_lineage dikeluarkan dari himpunan
eligible. Kueri tetap ada di indeks; hanya himpunan eligible yang berubah.
Ini BUKAN workload final, dan hasil dev tidak boleh dipakai sebagai hasil utama.
Timeout (DL-19) diambil dari run dengan --resource-profile lightsail, bukan dari laptop.

Jalankan dari root repo:  python -m src.benchmark.dev_benchmark
Output:  results/raw/dev_benchmark.jsonl  (satu baris per kueri x predikat x konfigurasi)
"""
from __future__ import annotations

import argparse
import itertools
import os
import subprocess
import time

import numpy as np
import pandas as pd

from src.groundtruth.exact_filtered_knn import exact_filtered_knn
from src.search.adaptivel import adaptivel_search
from src.search.graph_index import load_vamana_graph
from src.search.postfilter import postfilter_search
from src.search.twohop import twohop_search
from src.workload.build_queries import excluded_rows, exclusion_groups


# Predikat pengembangan: dua predikat layak (>= 100 titik) per bin B2-B5, dari tipe berbeda.
# exclude_ambiguous=True mengeluarkan berita ambigu (robustness check DT-3):
# predikat wilayah tanpa berita multi-kabupaten, predikat kategori tanpa berita multi-kategori
def dev_predicates(corpus: pd.DataFrame, exclude_ambiguous: bool = False) -> dict[str, np.ndarray]:
    has = lambda col, v: corpus[col].apply(lambda d: v in d).values
    news = (corpus["source_type"] == "news").values
    amb_region = news & corpus["region_ambiguous"].fillna(False).astype(bool).values
    amb_cat = news & (corpus["category"].map(len) > 1).values
    ok_region = ~amb_region if exclude_ambiguous else np.ones(len(corpus), bool)
    ok_cat = ~amb_cat if exclude_ambiguous else np.ones(len(corpus), bool)
    preds = {
        "B5|kategori=alam": has("category", "alam") & ok_cat,
        "B5|temporal>=2026-07-23": (corpus["published_at"] >= "2026-07-23").values,
        "B4|penerbit=detik.com": (corpus["publisher_id"] == "detik.com").values,
        "B4|provinsi=Bali": has("province", "Bali") & ok_region,
        "B3|penerbit=jawapos.com": (corpus["publisher_id"] == "jawapos.com").values,
        "B3|provinsi=Aceh": has("province", "Aceh") & ok_region,
        "B2|kabupaten=Tanggamus": has("kabupaten", "Kabupaten Tanggamus") & ok_region,
        "B2|kabupaten=Pangandaran∧alam": has("kabupaten", "Kabupaten Pangandaran") & has("category", "alam") & ok_region & ok_cat,
    }
    return preds


# Konfigurasi: setiap metode pada L_search 100/200/400 (kurva recall-biaya, README A1);
# P1 dengan n_sample 32/64 (harus lebih kecil dari jumlah titik yang dikunjungi, kira-kira L) dan m_max 1/2/4/8
def configs() -> list[dict]:
    out = [{"method": "postfilter", "candidate_budget": L} for L in (100, 200, 400)]
    # Pembanding adil untuk AdaptiveL (DT-4): budget setara kasus terburuk L x m_max
    out += [{"method": "postfilter", "candidate_budget": L * 8} for L in (100, 200, 400)]
    out += [{"method": "twohop", "L": L} for L in (100, 200, 400)]
    for L in (100, 200, 400):
        out.append({"method": "adaptivel", "L": L, "n_sample": 64, "m_max": 1})
        out += [{"method": "adaptivel", "L": L, "n_sample": n, "m_max": m}
                for m, n in itertools.product((2, 4, 8), (32, 64))]
    return out


# Himpunan eligible untuk satu kueri dengan aturan self-match yang sama dengan workload beku
def eligible_for_query(mask: np.ndarray, qi: int, dup_group: np.ndarray, lineage: np.ndarray) -> tuple[np.ndarray, int]:
    eligible = mask.copy()
    ex = excluded_rows(int(qi), dup_group, lineage)
    eligible[ex] = False
    return eligible, len(ex)


# Commit repo saat run, beserta penanda working tree belum di-commit
def git_commit() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                             check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], capture_output=True,
                               text=True, check=True).stdout.strip()
        return sha + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"


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
    ap.add_argument("--exclude-ambiguous", action="store_true",
                    help="robustness check DT-3: berita ambigu dikeluarkan dari himpunan eligible")
    ap.add_argument("--resource-profile", default="dev-local",
                    help="profil mesin yang dicatat di log, mis. dev-local atau lightsail-t3.xlarge")
    args = ap.parse_args()
    commit = git_commit()

    vectors = np.load("data/embeddings/base_vectors.npy")
    start, neighbors = load_vamana_graph("index/diskann/tourism")
    corpus = pd.read_parquet("data/processed/corpus.parquet")
    dup_group, lineage = exclusion_groups(corpus, vectors)
    preds = dev_predicates(corpus, args.exclude_ambiguous)
    # Pada robustness check, hanya predikat yang berubah karena eksklusi yang dijalankan
    if args.exclude_ambiguous:
        base = dev_predicates(corpus, False)
        preds = {f: m for f, m in preds.items() if not np.array_equal(m, base[f])}
        print("Predikat terdampak:", list(preds))
    query_idx = np.random.default_rng(args.seed).choice(len(vectors), size=args.n_queries, replace=False)

    rows = []
    for filter_id, mask in preds.items():
        match_rate = float(mask.mean())
        for qi in query_idx:
            # Himpunan eligible dengan aturan self-match workload, dan ground truth eksaknya
            eligible, n_excluded = eligible_for_query(mask, qi, dup_group, lineage)
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
                    "match_rate": match_rate, "k": args.k, "resource_profile": args.resource_profile,
                    "commit": commit, "seed": args.seed,
                    "self_match_exclusion": "query_document,identical_vector,same_story_lineage",
                    "n_excluded": n_excluded, "n_eligible": int(eligible.sum()),
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
