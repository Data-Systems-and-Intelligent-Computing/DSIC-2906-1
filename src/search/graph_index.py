"""Pembacaan graf DiskANN (Vamana) dan penelusuran greedy yang terinstrumentasi.

Graf dibangun sekali oleh src.index.build_diskann (diskannpy); modul ini hanya membaca
berkas graf yang sama sehingga seluruh metode memakai satu shared proximity graph
(Protokol bagian 19 butir 2). Penelusuran ditulis ulang di Python karena diskannpy
tidak membuka akses ke traversal (README bagian 32).
"""
from __future__ import annotations

import heapq
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


class Beam:
    """Frontier berukuran L: menyimpan L titik terdekat yang pernah ditemui.

    Setara dengan daftar terurut yang dipangkas ke L setelah setiap penambahan, tetapi
    memakai dua heap agar tetap cepat untuk L besar: `best` (max-heap L titik terbaik)
    dan `cand` (min-heap titik yang belum dikunjungi). Titik yang tersingkir dari frontier
    tidak pernah kembali, sama seperti pada daftar terurut.
    """

    def __init__(self, L: int, n_points: int):
        self.L = L
        self.best: list[tuple[float, int]] = []
        self.cand: list[tuple[float, int]] = []
        self.in_pool = np.zeros(n_points, dtype=bool)

    # Penambahan satu titik; titik yang lebih jauh dari L terbaik langsung dibuang
    def push(self, d: float, i: int) -> None:
        if len(self.best) < self.L:
            heapq.heappush(self.best, (-d, -i))
        elif (d, i) < (-self.best[0][0], -self.best[0][1]):
            _, out = heapq.heapreplace(self.best, (-d, -i))
            self.in_pool[-out] = False
        else:
            return
        self.in_pool[i] = True
        heapq.heappush(self.cand, (d, i))

    # Titik terdekat di frontier yang belum dikunjungi, atau None bila tidak ada
    def pop_unvisited(self) -> tuple[float, int] | None:
        while self.cand:
            d, i = heapq.heappop(self.cand)
            if self.in_pool[i]:
                return d, i
        return None

    # Isi frontier terurut dari yang terdekat
    def items(self) -> list[tuple[float, int]]:
        return sorted((-d, -i) for d, i in self.best)


# Penelusuran greedy (beam search) dengan pencatatan biaya pencarian
def greedy_search(query: np.ndarray, vectors: np.ndarray, neighbors: list[np.ndarray], start: int,
                  L: int) -> tuple[list[tuple[float, int]], dict]:
    """Penelusuran greedy Vamana dengan frontier berukuran L.

    Jarak = 1 - cosine (vektor sudah dinormalisasi, sehingga cosine = perkalian titik).
    Kembalikan isi frontier terurut [(jarak, id), ...] dan statistik biaya
    (visited_nodes, distance_comparisons) untuk README bagian 25.
    """
    seen = np.zeros(len(vectors), dtype=bool)
    seen[start] = True
    beam = Beam(L, len(vectors))
    beam.push(float(1.0 - vectors[start] @ query), start)
    n_visited, n_dist = 0, 1

    while (top := beam.pop_unvisited()) is not None:
        _, nxt = top
        n_visited += 1

        # Tetangga yang belum pernah dihitung jaraknya
        nb = neighbors[nxt]
        new = nb[~seen[nb]]
        if len(new):
            seen[new] = True
            d = 1.0 - vectors[new] @ query
            n_dist += len(new)
            for dist, i in zip(d.tolist(), new.tolist()):
                beam.push(dist, i)

    return beam.items(), {"visited_nodes": n_visited, "distance_comparisons": n_dist}
