"""Uji cepat bahwa DiskANN terpasang dan bisa membangun + mencari indeks.

Jalankan di dalam container Docker:  python scripts/check_diskann.py
Data acak, tidak menyentuh data penelitian.
"""
from __future__ import annotations

import platform
import tempfile

import numpy as np
import diskannpy


def main() -> None:
    # Info lingkungan
    print("Platform :", platform.machine(), platform.system())
    print("Python   :", platform.python_version())

    # Data acak kecil (2.000 titik, dimensi 384 seperti MiniLM)
    rng = np.random.default_rng(2906)
    x = rng.random((2000, 384), dtype=np.float32)

    # Bangun indeks dengan parameter jangkar dari configs/diskann.yaml (R=64, L=100)
    idx_dir = tempfile.mkdtemp()
    diskannpy.build_memory_index(
        x, distance_metric="cosine", index_directory=idx_dir,
        complexity=100, graph_degree=64, num_threads=1,
    )

    # Cari 10 tetangga terdekat dari titik ke-0
    index = diskannpy.StaticMemoryIndex(
        index_directory=idx_dir, num_threads=1, initial_search_complexity=100,
    )
    res = index.search(x[0], k_neighbors=10, complexity=100)

    # Titik ke-0 seharusnya menemukan dirinya sendiri di urutan pertama
    assert res.identifiers[0] == 0, "Hasil tidak wajar: titik 0 tidak menemukan dirinya"
    print("Hasil top-5:", res.identifiers[:5].tolist())
    print("DiskANN OK")


if __name__ == "__main__":
    main()
