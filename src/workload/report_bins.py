"""
report_bins.py
Melaporkan median dan rentang match rate aktual per bin (gate tahap awal, protokol bagian 21; Notion No 42).
Dihitung dari workload yang benar-benar dipakai (data/processed/workload.parquet), dipisah set utama dan ekstensi.
match_rate = n_eligible_raw / jumlah titik korpus (sebelum eksklusi self-match per kueri).

Keluaran:
  results/tables/match_rate_per_bin.csv
"""

import os

import pandas as pd

# Lokasi berkas
WORKLOAD_PATH = "data/processed/workload.parquet"
OUT_PATH = "results/tables/match_rate_per_bin.csv"

w = pd.read_parquet(WORKLOAD_PATH)

# Ringkasan per set (utama/ekstensi) dan bin
tabel = w.groupby(["set", "bin"]).agg(
    n_pasangan=("pair_id", "size"),
    n_predikat=("filter_id", "nunique"),
    n_tipe_predikat=("type", "nunique"),
    mr_median_pct=("match_rate", "median"),
    mr_min_pct=("match_rate", "min"),
    mr_max_pct=("match_rate", "max"),
    eligible_min_setelah_eksklusi=("n_eligible", "min"),
)

# Konversi match rate ke persen agar sebanding dengan batas bin di configs/workload.yaml
kolom_pct = ["mr_median_pct", "mr_min_pct", "mr_max_pct"]
tabel[kolom_pct] = (tabel[kolom_pct] * 100).round(4)

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
tabel.to_csv(OUT_PATH)
print(tabel.to_string())