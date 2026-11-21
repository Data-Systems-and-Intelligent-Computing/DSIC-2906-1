import numpy as np

from src.search.adaptivel import adaptivel_search, compute_adaptive_multiplier


def test_adaptivel_scaling_anchor_cases():
    assert compute_adaptive_multiplier(0.0, 8) == 8
    assert compute_adaptive_multiplier(0.5, 8) == 1
    assert compute_adaptive_multiplier(0.1, 8) == 2
    assert compute_adaptive_multiplier(0.01, 8) == 4


# Graf lengkap kecil: setiap titik terhubung ke semua titik lain
def _data_lengkap(n=40, seed=0):
    rng = np.random.default_rng(seed)
    vectors = rng.normal(size=(n, 8)).astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    neighbors = [np.array([j for j in range(n) if j != i], dtype=np.int64) for i in range(n)]
    return vectors, neighbors


def test_adaptivel_scales_L_when_sample_has_no_match():
    vectors, neighbors = _data_lengkap()
    # Satu-satunya titik yang lolos adalah titik terjauh dari kueri, jadi sampel awal tidak memuatnya
    jarak = 1.0 - vectors @ vectors[0]
    terjauh = int(np.argmax(jarak))
    eligible = np.zeros(40, dtype=bool)
    eligible[terjauh] = True
    _, stats = adaptivel_search(vectors[0], vectors, neighbors, 0, eligible, k=1, L=4, n_sample=3, m_max=8)
    assert stats["sample_reached"] and stats["sp_hat"] == 0
    assert stats["multiplier"] == 8 and stats["L_final"] == 32


def test_adaptivel_keeps_L_when_match_rate_is_high():
    vectors, neighbors = _data_lengkap()
    eligible = np.ones(40, dtype=bool)
    result, stats = adaptivel_search(vectors[0], vectors, neighbors, 0, eligible, k=3, L=4, n_sample=3, m_max=8)
    assert stats["multiplier"] == 1.0 and stats["L_final"] == 4
    assert len(result) == 3


def test_adaptivel_results_are_visited_eligible_points():
    vectors, neighbors = _data_lengkap()
    eligible = np.zeros(40, dtype=bool)
    eligible[::3] = True
    result, stats = adaptivel_search(vectors[0], vectors, neighbors, 0, eligible, k=5, L=8, n_sample=4, m_max=8)
    assert all(eligible[i] for i in result)
    assert stats["predicate_evaluations"] == stats["visited_nodes"]


def test_adaptivel_without_reaching_sample_never_scales():
    vectors, neighbors = _data_lengkap()
    eligible = np.zeros(40, dtype=bool)
    eligible[5] = True
    _, stats = adaptivel_search(vectors[0], vectors, neighbors, 0, eligible, k=1, L=4, n_sample=1000, m_max=8)
    assert not stats["sample_reached"] and stats["L_final"] == 4
