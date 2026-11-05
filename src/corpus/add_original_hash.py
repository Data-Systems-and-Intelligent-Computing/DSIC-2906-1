"""
add_original_hash.py
Menambahkan SHA-256 berkas JADESTA asli (data-jadesta.zip) ke kolom notes pada source_manifest.csv.
Berkas di data/raw/jadesta/ sudah dirapikan sebelum build_corpus.py (perapian provinsi, K-01),
sehingga checksum_sha256 mencatat versi turunan. Skema manifest tidak diubah.
"""

import os
import shutil

import pandas as pd

# Lokasi berkas masukan
MANIFEST_PATH = "data/manifests/source_manifest.csv"
HASH_CHECK_PATH = "data/reports/province_hash_check.csv"

# Cadangan manifest sebelum diubah
shutil.copy(MANIFEST_PATH, MANIFEST_PATH + ".bak")

manifest = pd.read_csv(MANIFEST_PATH)
hashes = pd.read_csv(HASH_CHECK_PATH)


# Pengambilan nama berkas dari path; sel kosong (NaN) dikembalikan sebagai string kosong
def nama_berkas(v):
    return os.path.basename(v) if isinstance(v, str) else ""


# Kolom nama berkas pada skema manifest dosen
kolom = "path_or_uri"
basename = manifest[kolom].map(nama_berkas)
peta_hash = dict(zip(hashes["source_file"], hashes["sha256_asli"]))


# Penambahan hash asli dan asal-usul ke kolom notes (skema manifest tidak diubah)
def tambah_catatan(row):
    b = nama_berkas(row[kolom])
    if b not in peta_hash:
        return row["notes"]
    lama = row["notes"] if isinstance(row["notes"], str) else ""
    baru = (f"turunan dari data-jadesta.zip (provinsi dirapikan sebelum build_corpus.py, "
            f"lihat normalization_report.csv); sha256_asli={peta_hash[b]}")
    return baru if baru in lama else "; ".join(x for x in [lama, baru] if x)


manifest["notes"] = manifest.apply(tambah_catatan, axis=1)
manifest.to_csv(MANIFEST_PATH, index=False)

# Ringkasan hasil
n = basename.isin(peta_hash.keys()).sum()
print("Berkas diberi hash asli:", int(n), "dari", len(manifest))
print(manifest.loc[basename.isin(peta_hash.keys()), [kolom, "notes"]].to_string(max_colwidth=80))