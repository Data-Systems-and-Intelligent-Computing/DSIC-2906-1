import numpy as np

from src.search.twohop import twohop_search


# Tujuh titik pada lingkaran satuan; graf bintang dengan titik 0 sebagai pusat dan rantai 1-2, 3-4, 5-6
def _data_bintang():
    sudut = np.linspace(0, np.pi, 7)
    vectors = np.stack([np.cos(sudut), np.sin(sudut)], axis=1).astype(np.float32)
    neighbors = [np.array(n, dtype=np.int64) for n in
                 [[1, 3, 5], [0, 2], [1], [0, 4], [3], [0, 6], [5]]]
    return vectors, neighbors


def test_twohop_returns_only_eligible_points():
    vectors, neighbors = _data_bintang()
    eligible = np.array([False, True, True, False, True, False, True])
    result, stats = twohop_search(vectors[6], vectors, neighbors, 0, eligible, k=3, L=5)
    assert all(eligible[i] for i in result)
    assert stats["returned_count"] == 3


def test_twohop_expands_when_most_neighbors_fail_predicate():
    vectors, neighbors = _data_bintang()
    # Hanya titik 6 yang lolos; ketiga tetangga pusat (1, 3, 5) gagal -> |U| = 3 > 3/2
    eligible = np.zeros(7, dtype=bool)
    eligible[6] = True
    result, stats = twohop_search(vectors[6], vectors, neighbors, 0, eligible, k=1, L=5)
    assert result == [6]                      # ditemukan lewat dua-hop (0 -> 5 -> 6)
    assert stats["twohop_expansions"] >= 1


def test_twohop_skips_expansion_when_most_neighbors_pass():
    vectors, neighbors = _data_bintang()
    # Titik 1 dan 3 lolos: di pusat |U| = 1 (titik 5), di titik 1 dan 3 |U| = 1 dari 2 tetangga;
    # tidak ada kunjungan dengan |U| > |N_out| / 2, sehingga dua-hop tidak pernah dipakai
    eligible = np.array([False, True, False, True, False, False, False])
    result, stats = twohop_search(vectors[1], vectors, neighbors, 0, eligible, k=2, L=5)
    assert stats["twohop_expansions"] == 0
    assert sorted(result) == [1, 3]
