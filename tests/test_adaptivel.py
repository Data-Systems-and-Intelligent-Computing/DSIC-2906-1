from src.search.adaptivel import compute_adaptive_multiplier


def test_adaptivel_scaling_anchor_cases():
    assert compute_adaptive_multiplier(0.0, 8) == 8
    assert compute_adaptive_multiplier(0.5, 8) == 1
    assert compute_adaptive_multiplier(0.1, 8) == 2
    assert compute_adaptive_multiplier(0.01, 8) == 4
