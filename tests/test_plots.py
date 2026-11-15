"""Grafik wajib dibuat dari tabel laporan sintetis tanpa galat."""
import pandas as pd

from src.evaluation.plots import (match_rate_plots, sp_hat_vs_match_rate, recall_cost_curves, recall_latency_curve,
                                  recall_qps_curve, single_vs_compound, stability_plot)


# Tabel laporan sintetis: dua bin, satu tipe tunggal dan satu majemuk, tiga metode
def _table():
    rows = []
    for b in ("B2", "B3"):
        for t in ("kabupaten", "kabupaten_kategori"):
            for m in ("postfilter", "twohop", "adaptivel"):
                rows.append({"bin": b, "type": t, "method": m, "config": m + "_maks",
                             "recall_mean": 0.7, "qps": 50.0, "stability_overlap": 1.0,
                             "p95_ms": 20.0, "dist_comp_median": 500.0, "pred_eval_median": 300.0})
    cpm = {m: m + "_maks" for m in ("postfilter", "twohop", "adaptivel")}
    return pd.DataFrame(rows), cpm


def test_semua_grafik_tertulis(tmp_path):
    table, cpm = _table()
    paths = [recall_qps_curve(table, "B2", tmp_path),
             single_vs_compound(table, {"kabupaten_kategori"}, cpm, tmp_path),
             stability_plot(table, cpm, tmp_path)]
    assert all(p is not None and p.stat().st_size > 0 for p in paths)


def test_stabilitas_dilewati_tanpa_data(tmp_path):
    table, cpm = _table()
    assert stability_plot(table.drop(columns="stability_overlap"), cpm, tmp_path) is None


def test_grafik_tambahan_tertulis(tmp_path):
    table, cpm = _table()
    per_mr = pd.DataFrame([{"mr_group": g, "method": m, "config": m + "_maks", "match_rate_median": 0.001 * (g + 1),
                            "recall_mean": 0.5, "visited_median": 100.0}
                           for g in range(3) for m in ("postfilter", "twohop", "adaptivel")])
    paths = [recall_latency_curve(table, tmp_path), *recall_cost_curves(table, tmp_path),
             *match_rate_plots(per_mr, cpm, tmp_path)]
    assert len(paths) == 5 and all(p.stat().st_size > 0 for p in paths)



def test_grafik_sp_hat(tmp_path):
    sp = pd.DataFrame({"config": ["a"] * 4, "match_rate": [0.001, 0.01, 0.1, 0.5], "sp_hat": [0.0, 0.03125, 0.1, 0.6],
                       "query_in_filter": [True, False, True, False]})
    p = sp_hat_vs_match_rate(sp, "a", 32, tmp_path)
    assert p is not None and p.stat().st_size > 0
