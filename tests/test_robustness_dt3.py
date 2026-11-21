"""Robustness DT-3 opsi B: dokumen bernilai ganda pada kolom predikat keluar; predikat lain tidak disentuh."""
import json

import pandas as pd

from src.benchmark.main_benchmark import method_configs
from src.evaluation.robustness_dt3 import compare_with_main, multi_valued, robust_mask, run_robustness
from tests.test_main_benchmark import _cfg, _data


def _korpus():
    return pd.DataFrame({
        "source_type": ["news", "news", "jadesta_atraksi", "news"],
        "kabupaten": [["A", "B"], ["A"], ["A"], ["C"]],
        "province": [["P"], ["P"], ["P"], ["P", "Q"]],
        "category": [["alam"], ["alam", "budaya"], ["alam"], ["alam"]],
    })


def test_kabupaten_ganda_keluar_dari_filter_kabupaten():
    c = _korpus()
    assert robust_mask(c, {"kabupaten": "A"}, multi_valued(c)).tolist() == [False, True, True, False]


def test_provinsi_dinilai_dari_jumlah_provinsi_bukan_kabupaten():
    c = _korpus()
    # Dokumen 0 punya dua kabupaten tetapi satu provinsi: tetap lolos filter provinsi
    assert robust_mask(c, {"province": "P"}, multi_valued(c)).tolist() == [True, True, True, False]


def test_kategori_ganda_keluar_dan_predikat_majemuk():
    c = _korpus()
    assert robust_mask(c, {"category": "alam"}, multi_valued(c)).tolist() == [True, False, True, True]
    assert robust_mask(c, {"kabupaten": "A", "category": "alam"}, multi_valued(c)).tolist() == [False, False, True, False]


def test_predikat_tanpa_kolom_ganda_dilewati():
    c = _korpus()
    assert robust_mask(c, {"source_type": "news"}, multi_valued(c)) is None


def test_alur_lengkap_data_sintetis():
    corpus, v, nb, wl, _ = _data()
    n = len(corpus)
    # Setiap titik ke-4 diberi kategori ganda, sehingga keluar dari himpunan eligible
    corpus = corpus.assign(category=[["alam", "budaya"] if i % 4 == 0 else (["alam"] if i % 2 == 0 else ["budaya"])
                                     for i in range(n)])
    recs = pd.DataFrame(run_robustness(corpus, v, nb, 0, wl, method_configs(_cfg()), 10, None))
    assert set(recs["method"]) == {"postfilter", "twohop", "adaptivel"}
    assert (recs["n_eligible_robust"] < recs["n_eligible_main"]).all()
    main = recs[["pair_id", "config"]].assign(recall_at_10=1.0, underfilled=False)
    assert {"robust_vs_main", "cakupan"} <= set(compare_with_main(recs, main))
