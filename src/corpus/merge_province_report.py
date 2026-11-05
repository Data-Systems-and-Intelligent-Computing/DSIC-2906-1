"""
merge_province_report.py
Menggabungkan catatan perapian provinsi (province_normalization.csv) ke dalam
normalization_report.csv dengan format kolom yang sama: doc_id, column, before, after, rule.
doc_id diambil dari corpus.parquet lewat pasangan (source_file, row_index).
"""

import os
import shutil

import pandas as pd

# Lokasi berkas masukan dan keluaran
PROV_PATH = "data/reports/province_normalization.csv"
REPORT_PATH = "data/processed/normalization_report.csv"
CORPUS_PATH = "data/processed/corpus.parquet"

# Cadangan laporan lama sebelum diubah
shutil.copy(REPORT_PATH, REPORT_PATH + ".bak")

prov = pd.read_csv(PROV_PATH)
report = pd.read_csv(REPORT_PATH)
corpus = pd.read_parquet(CORPUS_PATH, columns=["doc_id", "source_file", "row_index"])

# Penyeragaman nama berkas (corpus bisa menyimpan path lengkap, laporan hanya nama berkas)
corpus["source_file"] = corpus["source_file"].map(os.path.basename)

# Pencocokan baris perapian ke doc_id korpus
merged = prov.merge(corpus, on=["source_file", "row_index"], how="left")
n_missing = merged["doc_id"].isna().sum()
assert n_missing == 0, f"{n_missing} baris tidak menemukan doc_id — cek basis row_index (0 vs 1)"

# Penyesuaian ke format kolom laporan normalisasi
new_rows = pd.DataFrame({
    "doc_id": merged["doc_id"],
    "column": "province",
    "before": merged["nilai_sebelum"],
    "after": merged["nilai_sesudah"],
    "rule": merged["aturan"] + " [dilakukan sebelum build_corpus.py; sumber asli: data-jadesta.zip]",
})

# Penghapusan baris provinsi lama (jika script pernah dijalankan) agar tidak dobel
report = report[report["column"] != "province"]
out = pd.concat([report, new_rows], ignore_index=True)
out.to_csv(REPORT_PATH, index=False)

# Ringkasan hasil
print("Baris laporan sebelum:", len(report), "| ditambah:", len(new_rows), "| total:", len(out))
print(out["column"].value_counts().to_string())