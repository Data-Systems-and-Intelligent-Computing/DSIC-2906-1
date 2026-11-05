"""Timeout per kueri (DL-19): perilaku tanpa batas tidak berubah, batas 0 berhenti segera."""
import numpy as np
import pytest

from src.search.adaptivel import adaptivel_search
from src.search.graph_index import deadline_from, expired, greedy_search
from src.search.postfilter import postfilter_search
from src.search.twohop import twohop_search


# Graf acak kecil: 300 titik ternormalisasi, 8 tetangga per titik, separuh titik eligible
def _data():
    rng = np.random.default_rng(0)
    vectors = rng.normal(size=(300, 16)).astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    neighbors = [rng.choice(np.delete(np.arange(300), i), size=8, replace=False) for i in range(300)]
    eligible = rng.random(300) < 0.5
    return vectors, neighbors, 0, eligible, vectors[5]


# Ketiga metode dengan parameter yang sama
def _metode():
    return [
        ("postfilter", lambda v, nb, s, e, q, t: postfilter_search(q, v, nb, s, e, 10, 100, timeout_ms=t)),
        ("twohop", lambda v, nb, s, e, q, t: twohop_search(q, v, nb, s, e, 10, 50, timeout_ms=t)),
        ("adaptivel", lambda v, nb, s, e, q, t: adaptivel_search(q, v, nb, s, e, 10, 50, 32, 8, timeout_ms=t)),
    ]


@pytest.mark.parametrize("nama,cari", _metode())
def test_tanpa_timeout_sama_dengan_timeout_besar(nama, cari):
    v, nb, s, e, q = _data()
    r0, st0 = cari(v, nb, s, e, q, None)
    r1, st1 = cari(v, nb, s, e, q, 1e7)
    assert r0 == r1
    assert st0["timeout"] is False and st1["timeout"] is False
    assert st0["visited_nodes"] == st1["visited_nodes"]


@pytest.mark.parametrize("nama,cari", _metode())
def test_timeout_nol_berhenti_segera(nama, cari):
    v, nb, s, e, q = _data()
    r, st = cari(v, nb, s, e, q, 0)
    assert st["timeout"] is True
    assert st["visited_nodes"] == 0
    assert all(e[i] for i in r)  # hasil parsial tetap memenuhi predikat


def test_greedy_search_mencatat_timeout():
    v, nb, s, _, q = _data()
    _, st = greedy_search(q, v, nb, s, L=50)
    assert st["timeout"] is False


def test_timeout_negatif_ditolak():
    with pytest.raises(ValueError):
        deadline_from(-1)


def test_expired_tanpa_tenggat_selalu_false():
    assert expired(None) is False
    assert expired(deadline_from(0)) is True
