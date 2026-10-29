"""Metrik stabilitas sesuai README bagian 26 dan integrasinya dengan runner."""
import pandas as pd
import pytest

from src.benchmark.main_benchmark import method_configs, run_pairs
from src.benchmark.stability import overlap_at_k, pair_stability, stability_table
from tests.test_main_benchmark import _cfg, _data


def test_overlap_dibagi_k():
    assert overlap_at_k([1, 2, 3], [1, 2, 3], k=10) == 0.3  # under-filled menurunkan overlap
    assert overlap_at_k(list(range(10)), list(range(10)), k=10) == 1.0
    assert overlap_at_k([1, 2], [3, 4], k=2) == 0.0


def test_overlap_hanya_k_teratas():
    assert overlap_at_k([1, 2, 9], [1, 2, 8], k=2) == 1.0


def test_pair_stability_butuh_dua_ulangan():
    with pytest.raises(ValueError):
        pair_stability([[1, 2]], k=2)
    assert pair_stability([[1, 2], [1, 2], [1, 3]], k=2) == pytest.approx((1 + 0.5 + 0.5) / 3)


def test_runner_berulang_deterministik():
    corpus, v, nb, wl, gt = _data()
    recs = run_pairs(corpus, v, nb, 0, wl, gt, method_configs(_cfg()), 10, None, {}, repeats=3)
    assert len(recs) == 2 * 3 * 3
    per_pair, ringkas = stability_table(pd.DataFrame(recs))
    assert (per_pair["n_repeat"] == 3).all()
    # Penelusuran tanpa timeout bersifat deterministik: overlap harus 1.0 (tetap dilaporkan apa adanya)
    assert (per_pair["overlap_at_k"] == 1.0).all()
