"""Grafik wajib dibuat dari tabel laporan sintetis tanpa galat."""
import pandas as pd

from src.evaluation.plots import recall_qps_curve, single_vs_compound, stability_plot


# Tabel laporan sintetis: dua bin, satu tipe tunggal dan satu majemuk, tiga metode
def _table():
    rows = []
    for b in ("B2", "B3"):
        for t in ("kabupaten", "kabupaten_kategori"):
            for m in ("postfilter", "twohop", "adaptivel"):
                rows.append({"bin": b, "type": t, "method": m, "config": m + "_maks",
                             "recall_mean": 0.7, "qps": 50.0, "stability_overlap": 1.0})
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