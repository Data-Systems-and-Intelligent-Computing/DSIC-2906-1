"""
province_diff.py
Mencatat perapian kolom provinsi (dilakukan sebelum build_corpus.py) ke dalam
laporan normalisasi, dengan membandingkan berkas JADESTA asli (dari zip dosen)
dan berkas hasil perapian, baris per baris.

Keluaran:
  data/reports/province_normalization.csv  -> satu baris per sel provinsi yang berubah
  data/reports/province_hash_check.csv     -> perbandingan SHA-256 berkas asli vs berkas di data/

Dijalankan dari root repo:
  python src/corpus/province_diff.py
"""

import glob
import hashlib
import os
import re

import pandas as pd

# Lokasi berkas: ORIG_DIR = hasil ekstrak zip dosen (tidak pernah diubah),
# TIDY_DIR = berkas yang sudah dirapikan dan dipakai build_corpus.py
ORIG_DIR = "data/_asli/data-jadesta"
TIDY_DIR = "data/raw/jadesta"
OUT_DIR = "data/reports"

# Pola teks penghargaan yang salah masuk ke kolom provinsi (temuan T-02)
ADWI_PATTERN = re.compile(r"^\d+ Besar ADWI \d{4}$")


# Menghitung SHA-256 sebuah berkas secara bertahap agar hemat memori
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# Mengubah nilai sel menjadi string bersih; NaN/kosong menjadi None
def clean(v):
    if pd.isna(v):
        return None
    s = str(v).strip()
    return s if s else None


# Menentukan aturan perapian berdasarkan nilai sebelum dan sesudah
def classify(before, after):
    if before is not None and ADWI_PATTERN.match(before):
        return "T-02: teks ADWI di kolom provinsi diganti provinsi hasil pemetaan kabupaten"
    if before is None:
        return "K-01: provinsi kosong diisi dari pemetaan kabupaten->provinsi"
    if after is None:
        return "provinsi dikosongkan"
    return "provinsi dibakukan/diganti sesuai pemetaan kabupaten->provinsi"


os.makedirs(OUT_DIR, exist_ok=True)

files = sorted(
    glob.glob(os.path.join(ORIG_DIR, "wisata_*.csv"))
    + glob.glob(os.path.join(ORIG_DIR, "desa_wisata_*.csv"))
)
assert files, f"Tidak ada berkas asli di {ORIG_DIR} — ekstrak zip dosen ke sana dulu."

report_rows = []
hash_rows = []

for orig_path in files:
    name = os.path.basename(orig_path)
    tidy_path = os.path.join(TIDY_DIR, name)

    # Perbandingan hash: apakah berkas di data/ masih identik dengan aslinya
    h_orig, h_tidy = sha256(orig_path), sha256(tidy_path)
    hash_rows.append({
        "source_file": name,
        "sha256_asli": h_orig,
        "sha256_data": h_tidy,
        "identik": h_orig == h_tidy,
    })

    orig = pd.read_csv(orig_path, low_memory=False)
    tidy = pd.read_csv(tidy_path, low_memory=False)

    # Pemeriksaan keselarasan baris: perbandingan per posisi hanya sah bila
    # jumlah baris sama dan kolom kabupaten tidak berubah urutannya
    assert len(orig) == len(tidy), f"{name}: jumlah baris berbeda ({len(orig)} vs {len(tidy)})"
    assert (orig["kabupaten"].fillna("") == tidy["kabupaten"].fillna("")).all(), \
        f"{name}: urutan/isi kabupaten berubah, baris tidak bisa dibandingkan per posisi"

    # Mencatat setiap sel provinsi yang nilainya berubah
    for i, (b, a) in enumerate(zip(orig["provinsi"], tidy["provinsi"])):
        before, after = clean(b), clean(a)
        if before != after:
            report_rows.append({
                "identifier": f"{name}:{i}",
                "source_file": name,
                "row_index": i,
                "kabupaten": clean(tidy.at[i, "kabupaten"]),
                "kolom": "provinsi",
                "nilai_sebelum": before,
                "nilai_sesudah": after,
                "aturan": classify(before, after),
                "pelaksana": "perapian manual dibantu Antigravity (sebelum build_corpus.py)",
            })

report = pd.DataFrame(report_rows)
hashes = pd.DataFrame(hash_rows)

report.to_csv(os.path.join(OUT_DIR, "province_normalization.csv"), index=False)
hashes.to_csv(os.path.join(OUT_DIR, "province_hash_check.csv"), index=False)

# Ringkasan hasil di terminal
print("Sel provinsi berubah:", len(report))
print(report["aturan"].value_counts().to_string())
print("\nPer berkas:")
print(report["source_file"].value_counts().sort_index().to_string())
print("\nBerkas di data/ yang TIDAK identik dengan aslinya:",
      int((~hashes["identik"]).sum()), "dari", len(hashes))

# Pemeriksaan konsistensi hasil perapian: setiap kabupaten harus ke tepat satu provinsi
all_tidy = pd.concat(
    [pd.read_csv(os.path.join(TIDY_DIR, os.path.basename(f)), low_memory=False) for f in files]
)
multi = all_tidy.groupby("kabupaten")["provinsi"].nunique()
print("Kabupaten dengan >1 provinsi:", int((multi > 1).sum()))
