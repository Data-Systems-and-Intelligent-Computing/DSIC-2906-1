"""Runner benchmark utama: pengaman pembekuan, field log wajib, dan recall pada data sintetis."""
import json

import numpy as np
import pandas as pd
import pytest

from src.benchmark.main_benchmark import check_frozen, method_configs, run_pairs
from src.benchmark.runner import REQUIRED_LOG_FIELDS
from src.groundtruth.exact_filtered_knn import exact_filtered_knn


# Korpus sintetis: 200 titik, separuh berkategori "alam", graf acak 10 tetangga
def _data():
    rng = np.random.default_rng(1)
    n = 200
    vectors = rng.normal(size=(n, 16)).astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    neighbors = [rng.choice(np.delete(np.arange(n), i), size=10, replace=False) for i in range(n)]
    corpus = pd.DataFrame({"category": [["alam"] if i % 2 == 0 else ["budaya"] for i in range(n)]})
    fid = json.dumps({"category": "alam"})
    mask = np.array([i % 2 == 0 for i in range(n)])
    rows, gts = [], []
    for j, qi in enumerate([3, 8]):
        ex = [qi]
        eligible = mask.copy(); eligible[ex] = False
        gt = exact_filtered_knn(vectors, vectors[qi], eligible, k=10)
        rows.append({"pair_id": f"P{j}", "set": "utama", "bin": "B5", "type": "kategori", "filter_id": fid,
                     "n_eligible": int(eligible.sum()), "match_rate": float(mask.mean()), "query_row": qi,
                     "excluded_rows": ex})
        gts.append({"pair_id": f"P{j}", "gt_rows": gt.tolist()})
    return corpus, vectors, neighbors, pd.DataFrame(rows), pd.DataFrame(gts)


def _cfg(frozen=True):
    return {"frozen": frozen, "k": 10, "methods": {
        "postfilter": {"candidate_budget": [200]}, "twohop": {"L": [200]},
        "adaptivel": {"L": [200], "n_sample": 32, "m_max": 8}}}


def test_menolak_bila_belum_beku():
    with pytest.raises(SystemExit):
        check_frozen(_cfg(frozen=False))


def test_menolak_parameter_kosong():
    c = _cfg(); c["methods"]["twohop"]["L"] = [None]
    with pytest.raises(SystemExit):
        check_frozen(c)


def test_semua_field_wajib_dan_recall():
    corpus, v, nb, wl, gt = _data()
    recs = run_pairs(corpus, v, nb, 0, wl, gt, method_configs(_cfg()), 10, None, {"resource_profile": "uji"})
    assert len(recs) == 2 * 3
    for r in recs:
        assert all(f in r for f in REQUIRED_LOG_FIELDS)
        assert 0.0 <= r["recall_at_10"] <= 1.0 and r["timeout"] is False
    # Graf kecil dengan L=200 menjelajah seluruh titik: recall harus sempurna
    assert all(r["recall_at_10"] == 1.0 for r in recs if r["method"] != "postfilter")


def test_eligible_tidak_cocok_dihentikan():
    corpus, v, nb, wl, gt = _data()
    wl.loc[0, "n_eligible"] += 1
    with pytest.raises(AssertionError):
        run_pairs(corpus, v, nb, 0, wl, gt, method_configs(_cfg()), 10, None, {})


def test_timeout_nol_tercatat():
    corpus, v, nb, wl, gt = _data()
    recs = run_pairs(corpus, v, nb, 0, wl, gt, method_configs(_cfg()), 10, 0, {})
    assert all(r["timeout"] is True for r in recs)
