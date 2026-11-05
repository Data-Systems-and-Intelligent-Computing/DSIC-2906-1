import struct

import numpy as np

from src.search.graph_index import greedy_search, load_vamana_graph
from src.search.postfilter import postfilter_search


# Graf kecil dalam format berkas Vamana: header 24 byte + (jumlah tetangga, id tetangga) per titik
def _tulis_graf(path, start, adjacency):
    body = b"".join(struct.pack("<I", len(n)) + struct.pack(f"<{len(n)}I", *n) for n in adjacency)
    size = 24 + len(body)
    with open(path, "wb") as f:
        f.write(struct.pack("<QIIQ", size, max(len(n) for n in adjacency), start, 0) + body)


# Lima titik pada lingkaran satuan, terhubung sebagai rantai 0-1-2-3-4
def _data_kecil(tmp_path):
    sudut = np.linspace(0, np.pi, 5)
    vectors = np.stack([np.cos(sudut), np.sin(sudut)], axis=1).astype(np.float32)
    adjacency = [[1], [0, 2], [1, 3], [2, 4], [3]]
    path = tmp_path / "graf"
    _tulis_graf(path, 0, adjacency)
    return vectors, str(path)


def test_load_vamana_graph_reads_header_and_neighbors(tmp_path):
    vectors, path = _data_kecil(tmp_path)
    start, neighbors = load_vamana_graph(path)
    assert start == 0
    assert [n.tolist() for n in neighbors] == [[1], [0, 2], [1, 3], [2, 4], [3]]


def test_greedy_search_reaches_nearest_point(tmp_path):
    vectors, path = _data_kecil(tmp_path)
    start, neighbors = load_vamana_graph(path)
    pool, stats = greedy_search(vectors[4], vectors, neighbors, start, L=2)
    assert pool[0][1] == 4                      # titik terdekat ditemukan walau mulai dari ujung lain
    assert stats["distance_comparisons"] == 5   # setiap titik dihitung jaraknya tepat sekali


def test_postfilter_returns_only_eligible_and_flags_underfill(tmp_path):
    vectors, path = _data_kecil(tmp_path)
    start, neighbors = load_vamana_graph(path)
    eligible = np.array([True, False, True, False, False])
    result, stats = postfilter_search(vectors[4], vectors, neighbors, start, eligible, k=3, candidate_budget=5)
    assert all(eligible[i] for i in result)
    assert stats["returned_count"] == 2 and stats["underfilled"]