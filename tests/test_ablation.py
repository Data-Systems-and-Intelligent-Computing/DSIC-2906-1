"""Tabel ablasi AdaptiveL dari log dev sintetis."""
import itertools

import pandas as pd

from src.evaluation.ablation import ablation_table


# Log dev sintetis: AdaptiveL dengan 2 x 2 x 2 kombinasi parameter, dua bin, ditambah baris metode lain
def _dev_log():
    rows = []
    for L, ns, mm, b in itertools.product([100, 400], [32, 64], [2, 8], ["B2", "B5"]):
        for q in range(3):
            rows.append({"method": "adaptivel", "L": L, "n_sample": ns, "m_max": mm, "bin": b,
                         "recall_at_10": 0.1 * mm + (0.5 if b == "B5" else 0.0),
                         "distance_comparisons": L * mm, "latency_ms": 1.0 + q})
    rows.append({"method": "twohop", "L": 100, "n_sample": None, "m_max": None, "bin": "B2",
                 "recall_at_10": 1.0, "distance_comparisons": 50, "latency_ms": 1.0})
    return pd.DataFrame(rows)


def test_satu_baris_per_kombinasi_adaptivel():
    t = ablation_table(_dev_log())
    # 2 L x 2 n_sample x 2 m_max = 8 baris; baris TwoHop tidak ikut
    assert len(t) == 8
    assert {"recall_B2", "recall_B5", "dist_median", "lat_p99_ms"} <= set(t.columns)


def test_nilai_recall_dan_biaya():
    t = ablation_table(_dev_log()).set_index(["L", "n_sample", "m_max"])
    r = t.loc[(400, 32, 8)]
    assert r["recall_B2"] == 0.8 and r["recall_B5"] == 1.3
    assert r["dist_median"] == 3200