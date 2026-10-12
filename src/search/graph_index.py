"""Pembacaan graf DiskANN (Vamana) dan penelusuran greedy yang terinstrumentasi.

Graf dibangun sekali oleh src.index.build_diskann (diskannpy); modul ini hanya membaca
berkas graf yang sama sehingga seluruh metode memakai satu shared proximity graph
(Protokol bagian 19 butir 2). Penelusuran ditulis ulang di Python karena diskannpy
tidak membuka akses ke traversal (README bagian 32).
"""
from __future__ import annotations

import os
import struct

import numpy as np


# Pembacaan berkas graf Vamana hasil build DiskANN
def load_vamana_graph(path: str) -> tuple[int, list[np.ndarray]]:
    """Kembalikan (titik_awal, daftar_tetangga) dari berkas graf DiskANN in-memory.

    Format berkas: header 24 byte (uint64 ukuran berkas, uint32 derajat maksimum,
    uint32 titik awal, uint64 jumlah frozen point), lalu untuk setiap titik:
    uint32 jumlah tetangga diikuti id tetangga (uint32).
    """
    with open(path, "rb") as f:
        expected_size, _max_degree, start, _frozen = struct.unpack("<QIIQ", f.read(24))
        raw = np.frombuffer(f.read(), dtype=np.uint32)
    if expected_size != os.path.getsize(path):
        raise ValueError(f"Ukuran berkas graf {os.path.getsize(path)} tidak sesuai header {expected_size}")

    neighbors: list[np.ndarray] = []
    pos = 0
    while pos < len(raw):
        k = int(raw[pos])
        neighbors.append(raw[pos + 1: pos + 1 + k].astype(np.int64))
        pos += 1 + k
    return int(start), neighbors


# Penelusuran greedy (beam search) dengan pencatatan biaya pencarian
def greedy_search(query: np.ndarray, vectors: np.ndarray, neighbors: list[np.ndarray], start: int,
                  L: int) -> tuple[list[tuple[float, int]], dict]:
    """Penelusuran greedy Vamana dengan daftar kandidat berukuran L.

    Jarak = 1 - cosine (vektor sudah dinormalisasi, sehingga cosine = perkalian titik).
    Kembalikan daftar kandidat terurut [(jarak, id), ...] dan statistik biaya
    (visited_nodes, distance_comparisons) untuk README bagian 25.
    """
    seen = {start}
    pool = [(float(1.0 - vectors[start] @ query), start)]
    expanded: set[int] = set()
    n_dist = 1

    while True:
        # Kandidat terdekat yang belum dikembangkan
        nxt = next((i for _, i in pool if i not in expanded), None)
        if nxt is None:
            break
        expanded.add(nxt)

        # Tetangga yang belum pernah dihitung jaraknya
        new = [int(j) for j in neighbors[nxt] if j not in seen]
        if new:
            seen.update(new)
            d = 1.0 - vectors[new] @ query
            n_dist += len(new)
            pool.extend(zip(d.tolist(), new))
            pool.sort()
            del pool[L:]

    return pool, {"visited_nodes": len(expanded), "distance_comparisons": n_dist}