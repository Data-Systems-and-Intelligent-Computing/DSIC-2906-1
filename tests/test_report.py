"""Tabel hasil utama (README bagian 43) dari log sintetis runner."""
import pandas as pd

from src.benchmark.main_benchmark import method_configs, run_pairs
from src.evaluation.bootstrap import mean_ci
from src.evaluation.report import main_table
from tests.test_main_benchmark import _cfg, _data


# Log sintetis dengan format yang sama dengan JSONL runner benchmark utama
def _log(repeats=1):
    corpus, v, nb, wl, gt = _data()
    recs = run_pairs(corpus, v, nb, 0, wl, gt, method_configs(_cfg()), 10, None, {}, repeats=repeats)
    return pd.DataFrame(recs)


def test_satu_baris_per_metode_konfigurasi():
    t = main_table(_log())
    assert len(t) == 3
    assert set(t["method"]) == {"postfilter", "twohop", "adaptivel"}
    assert (t["n_pasangan"] == 2).all()


def test_ci_mengapit_rata_rata():
    t = main_table(_log())
    assert (t["recall_ci_low"] <= t["recall_mean"]).all()
    assert (t["recall_mean"] <= t["recall_ci_high"]).all()


def test_ulangan_tidak_menggandakan_pasangan():
    # Dengan 3 ulangan, jumlah pasangan tetap 2 (bukan 6)
    t = main_table(_log(repeats=3))
    assert (t["n_pasangan"] == 2).all()


def test_mean_ci_dengan_variasi():
    m, (lo, hi) = mean_ci([0.0, 0.5, 1.0, 1.0])
    assert m == 0.625
    assert lo < m < hi