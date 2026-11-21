"""Tabel hasil utama (README bagian 43) dari log sintetis runner."""
import pandas as pd

from src.benchmark.main_benchmark import method_configs, run_pairs
from src.evaluation.bootstrap import mean_ci
from src.evaluation.report import (adaptivel_multiplier, adaptivel_sp_hat, main_table, paired_comparisons,
                                   per_match_rate, visited_per_L)
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

def test_pemecahan_per_query_in_filter():
    log = _log()
    # Satu pasangan di dalam filter, satu di luar
    log["query_in_filter"] = log["pair_id"].map({"P0": True, "P1": False})
    t = main_table(log, extra_groups=["query_in_filter"])
    assert len(t) == 3 * 2
    assert (t["n_pasangan"] == 1).all()


def test_build_report_dengan_stabilitas():
    from src.benchmark.stability import stability_table
    from src.evaluation.report import build_report
    log = _log(repeats=3)
    per_pair, _ = stability_table(log)
    t = build_report(log, per_pair)
    assert set(t) == {"main_table", "per_query_in_filter", "per_sumber_kueri", "failure_taxonomy",
                      "per_match_rate", "paired_comparisons", "visited_per_L", "adaptivel_multiplier",
                      "adaptivel_sp_hat"}
    # Penelusuran tanpa timeout deterministik, jadi overlap 1.0
    assert (t["main_table"]["stability_overlap"] == 1.0).all()
    assert (t["main_table"]["stability_identical"] == 1.0).all()


def test_kolom_biaya_jarak_dan_match_rate():
    log = _log()
    assert "dist_comp_median" in main_table(log)
    t = per_match_rate(log)
    assert set(t["method"]) == {"postfilter", "twohop", "adaptivel"}
    assert (t["n_pasangan"] >= 1).all()



def test_kolom_p95_dan_predikat():
    t = main_table(_log())
    for c in ["visited_p95", "dist_comp_p95", "pred_eval_p95", "predicate_satisfaction_pct"]:
        assert c in t
    assert (t["predicate_satisfaction_pct"] == 100.0).all()


def test_selisih_berpasangan():
    # Log sintetis: dua pasangan, AdaptiveL selalu 0,2 di atas TwoHop, sama dengan PostFilter 800
    rows = []
    for pid in ("P1", "P2", "P3"):
        for cfg, r in [("method=adaptivel L=100 n_sample=32 m_max=8", 0.8), ("method=twohop L=100", 0.6),
                       ("method=postfilter candidate_budget=800", 0.8)]:
            rows.append({"bin": "B2", "pair_id": pid, "config": cfg, "recall_at_10": r})
    t = paired_comparisons(pd.DataFrame(rows), L_values=(100,))
    th = t[t["pembanding"].str.contains("TwoHop")].iloc[0]
    pf = t[t["pembanding"].str.contains("PostFilter")].iloc[0]
    assert abs(th["selisih_recall"] - 0.2) < 1e-9 and th["arah"] == "a > b"
    assert pf["selisih_recall"] == 0 and pf["arah"] == "tidak berbeda"



def test_diagnostik_adaptivel_dan_rasio_L():
    log = _log()
    v = visited_per_L(log)
    assert set(v["method"]) == {"postfilter", "twohop", "adaptivel"}
    assert (v["rasio_median"] > 0).all()
    m = adaptivel_multiplier(log)
    kolom = ["pengali_1_pct", "pengali_sampai_2_pct", "pengali_2_sampai_max_pct", "pengali_max_pct"]
    # Keempat kelompok pengali saling lepas dan lengkap
    assert ((m[kolom].sum(axis=1) - 100).abs() < 1e-9).all()
    assert len(adaptivel_sp_hat(log)) == log[log["method"] == "adaptivel"]["pair_id"].nunique()


def test_evaluasi_unik_twohop():
    t = main_table(_log())
    tw = t[t["method"] == "twohop"]["pred_eval_unique_median"]
    assert tw.notna().all()
    assert (tw <= t[t["method"] == "twohop"]["pred_eval_median"]).all()
