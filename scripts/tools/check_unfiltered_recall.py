"""Pemeriksaan E1 (README bagian 28): recall@10 tanpa filter dari penelusuran graf versi Python.

Penelusuran Python (src/search) dipakai oleh ketiga metode, sedangkan angka 0,9959 di index_manifest.json
berasal dari diskannpy. Skrip ini memastikan keduanya setara pada graf yang sama.
Hanya membaca; hasil ditulis ke results/summary/unfiltered_recall_python.json.

Jalankan dari root repo:  python scripts/tools/check_unfiltered_recall.py [--n 300] [--L 100]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

# Root repo dimasukkan ke sys.path agar modul src bisa diimpor saat skrip dijalankan langsung
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.search.graph_index import load_vamana_graph  # noqa: E402
from src.search.postfilter import postfilter_search  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300, help="jumlah kueri acak dari korpus")
    ap.add_argument("--L", type=int, default=100)
    ap.add_argument("--seed", type=int, default=2906)
    args = ap.parse_args()

    v = np.load("data/embeddings/base_vectors.npy")
    start, nb = load_vamana_graph("index/diskann/tourism")
    qs = np.random.default_rng(args.seed).choice(len(v), args.n, replace=False)
    rec = []
    for qi in qs:
        q = v[qi]
        # Self-match dikeluarkan, sama seperti aturan workload
        elig = np.ones(len(v), dtype=bool)
        elig[qi] = False
        d = 1 - v @ q
        d[qi] = np.inf
        # Ground truth eksak tanpa filter, seri dipecah dengan nomor baris terkecil
        gt = set(np.lexsort((np.arange(len(v)), d))[:10].tolist())
        # PostFilter dengan semua titik lolos = penelusuran greedy tanpa filter
        res, _ = postfilter_search(q, v, nb, start, elig, 10, args.L)
        rec.append(len(gt & set(res)) / 10)

    manifest = json.loads(Path("data/manifests/index_manifest.json").read_text(encoding="utf-8"))
    out = {"n_queries": args.n, "L": args.L, "seed": args.seed,
           "recall_at_10_python": round(float(np.mean(rec)), 4),
           "recall_at_10_diskannpy": manifest.get("sanity_unfiltered_recall_at_10")}
    Path("results/summary/unfiltered_recall_python.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
