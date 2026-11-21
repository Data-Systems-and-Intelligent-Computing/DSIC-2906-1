"""Pembangunan satu shared DiskANN (Vamana) graph untuk seluruh metode (Protokol bagian 19).

Dijalankan di dalam container Docker (diskannpy hanya tersedia untuk Linux x86_64):
    docker run --rm --platform linux/amd64 -v "$PWD":/workspace dsic2906-diskann \
        python -m src.index.build_diskann

Output:
    index/diskann/<prefix>*           berkas indeks DiskANN
    index/diskann/index_manifest.json parameter beku, waktu build, ukuran, memori, checksum, sanity recall
"""
from __future__ import annotations

import glob
import json
import os
import platform
import resource
import time
from datetime import datetime, timezone
from pathlib import Path

import diskannpy
import numpy as np
import yaml

from src.index.index_manifest import sha256_file


# Parameter DiskANN yang dibekukan (configs/diskann.yaml)
def load_config(path: str = "configs/diskann.yaml") -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


# Recall@k pencarian tanpa filter terhadap pencarian eksak, pada sampel vektor korpus
def unfiltered_recall(index, vectors: np.ndarray, k: int, complexity: int, n_sample: int = 1000,
                      seed: int = 2906) -> float:
    rng = np.random.default_rng(seed)
    qi = rng.choice(len(vectors), size=n_sample, replace=False)
    queries = vectors[qi]

    # Hasil ANN: k+1 tetangga, lalu titik kueri itu sendiri dibuang (mencegah self-match)
    ann = index.batch_search(queries, k_neighbors=k + 1, complexity=max(complexity, k + 1), num_threads=1)
    # Hasil eksak: perkalian titik = cosine karena vektor sudah dinormalisasi
    exact = np.argsort(-(queries @ vectors.T), axis=1)[:, : k + 1]

    hits = 0
    for row, q in enumerate(qi):
        a = [i for i in ann.identifiers[row] if i != q][:k]
        e = [i for i in exact[row] if i != q][:k]
        hits += len(set(a) & set(e))
    return hits / (n_sample * k)


def main() -> None:
    cfg = load_config()
    vectors = np.load("data/embeddings/base_vectors.npy").astype(np.float32)
    index_dir = os.path.dirname(cfg["index_prefix"])
    prefix = os.path.basename(cfg["index_prefix"])
    os.makedirs(index_dir, exist_ok=True)

    # Pembangunan graf dengan parameter beku; alpha null = bawaan DiskANN (1.2)
    t0 = time.time()
    diskannpy.build_memory_index(
        vectors,
        distance_metric=cfg["metric"],
        index_directory=index_dir,
        index_prefix=prefix,
        complexity=cfg["L_build"],
        graph_degree=cfg["R"],
        num_threads=cfg["build_threads"],
        alpha=cfg["alpha"] if cfg["alpha"] is not None else 1.2,
    )
    build_time = time.time() - t0

    # Berkas indeks, ukurannya, dan checksum untuk pembekuan
    files = sorted(f for f in glob.glob(os.path.join(index_dir, prefix + "*")) if os.path.isfile(f))
    index_bytes = sum(os.path.getsize(f) for f in files)
    checksums = {os.path.basename(f): sha256_file(f) for f in files}

    # Uji kewarasan E1: recall@10 pencarian tanpa filter (README bagian 28)
    index = diskannpy.StaticMemoryIndex(
        index_directory=index_dir, index_prefix=prefix,
        num_threads=cfg["threads"], initial_search_complexity=cfg["L_search"],
    )
    recall = unfiltered_recall(index, vectors, k=10, complexity=cfg["L_search"])

    # Memori puncak proses (Linux: ru_maxrss dalam KB)
    peak_bytes = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024

    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "diskannpy_version": getattr(diskannpy, "__version__", "0.7.0"),
        "platform": f"{platform.system()} {platform.machine()} | Python {platform.python_version()}",
        "n_vectors": int(vectors.shape[0]),
        "dimension": int(vectors.shape[1]),
        "params": {k: cfg[k] for k in ("metric", "R", "L_build", "L_search", "alpha", "threads", "build_threads")},
        "build_time_s": round(build_time, 2),
        "index_size_bytes": int(index_bytes),
        "peak_memory_bytes": int(peak_bytes),
        "vectors_checksum_sha256": sha256_file("data/embeddings/base_vectors.npy"),
        "index_files_sha256": checksums,
        "sanity_unfiltered_recall_at_10": round(recall, 4),
    }
    with open(os.path.join(index_dir, "index_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()