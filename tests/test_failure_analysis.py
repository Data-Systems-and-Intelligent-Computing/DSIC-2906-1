"""Pelabelan kegagalan dan tabel failure taxonomy (README E6)."""
import numpy as np
import pandas as pd

from src.benchmark.main_benchmark import method_configs, run_pairs
from src.evaluation.failure_analysis import _dominated, failure_taxonomy, label_failures, primary_label
from tests.test_main_benchmark import _cfg, _data


def _log(timeout_ms=None):
    corpus, v, nb, wl, gt = _data()
    return pd.DataFrame(run_pairs(corpus, v, nb, 0, wl, gt, method_configs(_cfg()), 10, timeout_ms, {}))


def test_prioritas_label():
    assert primary_label({"timeout": True, "underfilled": True, "recall_at_10": 0.0}) == "timeout"
    assert primary_label({"timeout": False, "underfilled": True, "recall_at_10": 0.0}) == "underfilled_topk"
    assert primary_label({"timeout": False, "underfilled": False, "recall_at_10": 0.3}) == "low_recall"
    assert primary_label({"timeout": False, "underfilled": False, "recall_at_10": 0.9}) == "ok"


def test_timeout_nol_semua_timeout():
    t = failure_taxonomy(label_failures(_log(timeout_ms=0)))
    assert (t["timeout"] == 100.0).all()


def test_persentase_berjumlah_100():
    t = failure_taxonomy(label_failures(_log()))
    kolom_label = [c for c in t.columns if c not in ("bin", "method", "n_baris")]
    assert np.allclose(t[kolom_label].sum(axis=1), 100.0)


def test_dominasi_duplikat():
    lineage = np.array(["s1", "s1", "s1", "", "s2"])
    assert _dominated([0, 1, 2, 3], lineage, None, 0.5) is True   # 3 dari 4 hasil satu lineage
    assert _dominated([0, 3, 4], lineage, None, 0.5) is False       # tiap lineage hanya muncul sekali