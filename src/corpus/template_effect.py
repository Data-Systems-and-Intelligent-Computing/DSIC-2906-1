"""
template_effect.py
Mengukur efek templat teks JADESTA pada vektor embedding (ancaman validitas, No 61).
Teks JADESTA disusun sesuai protokol bagian 16 butir 6 (nama + alamat + fasilitas + kategori),
sehingga kemiripan antar-dokumen sebagian ditentukan oleh templat. Script ini hanya MENGUKUR,
tidak mengubah korpus, embedding, maupun indeks.

Keluaran:
  data/reports/template_effect.csv   -> ringkasan per source_type
  data/reports/template_effect.json  -> ringkasan yang sama + metadata (commit, waktu)

Dijalankan dari root repo:
  python src/corpus/template_effect.py
"""

import glob
import json
import subprocess
from datetime import datetime, timezone

import numpy as np
import pandas as pd

# Lokasi berkas masukan dan keluaran
CORPUS_PATH = "data/processed/corpus.parquet"
VECTORS_GLOB = "data/**/base_vectors.npy"
OUT_CSV = "data/reports/template_effect.csv"
OUT_JSON = "data/reports/template_effect.json"
CHUNK = 2048  # jumlah baris per blok perkalian matriks (hemat memori)

# Pencarian berkas vektor (lokasinya bisa di data/vectors/ atau data/processed/)
vec_paths = glob.glob(VECTORS_GLOB, recursive=True)
assert len(vec_paths) == 1, f"base_vectors.npy ditemukan {len(vec_paths)} kali: {vec_paths}"

corpus = pd.read_parquet(CORPUS_PATH, columns=["doc_id", "source_type"])
X = np.load(vec_paths[0]).astype(np.float32)

# Pemeriksaan keselarasan: baris vektor ke-i harus milik dokumen korpus ke-i
assert len(X) == len(corpus), f"Jumlah vektor {len(X)} != jumlah dokumen {len(corpus)}"

# Normalisasi L2 agar perkalian titik = kemiripan cosine (aman walau vektor sudah ternormalisasi)
X /= np.linalg.norm(X, axis=1, keepdims=True)
src = corpus["source_type"].to_numpy()

# --- Ukuran 1: vektor identik ---------------------------------------------------
# Vektor dianggap identik bila byte-nya sama persis (sesuai temuan 772 vektor identik)
keys = pd.Series([row.tobytes() for row in X])
dup_mask = keys.duplicated(keep=False).to_numpy()

# --- Ukuran 2: kemiripan cosine ke tetangga terdekat (selain diri sendiri) -------
# Dihitung eksak, per blok, ke seluruh korpus dan ke dokumen bersumber sama
nn_all = np.empty(len(X), dtype=np.float32)
nn_same = np.empty(len(X), dtype=np.float32)
for start in range(0, len(X), CHUNK):
    end = min(start + CHUNK, len(X))
    S = X[start:end] @ X.T
    S[np.arange(end - start), np.arange(start, end)] = -np.inf  # buang kemiripan diri sendiri
    nn_all[start:end] = S.max(axis=1)
    for st in np.unique(src[start:end]):
        rows = np.where(src[start:end] == st)[0]
        nn_same[start + rows] = S[np.ix_(rows, np.where(src == st)[0])].max(axis=1)
    print(f"  blok {start:>6}-{end:<6} selesai", end="\r")
print()

# --- Ringkasan per source_type --------------------------------------------------
df = pd.DataFrame({"source_type": src, "dup": dup_mask, "nn_all": nn_all, "nn_same": nn_same})
summary = df.groupby("source_type").agg(
    n_dokumen=("dup", "size"),
    n_vektor_identik=("dup", "sum"),
    nn_cos_median=("nn_all", "median"),
    nn_cos_p90=("nn_all", lambda s: s.quantile(0.90)),
    nn_cos_ge_0_95=("nn_all", lambda s: (s >= 0.95).mean()),
    nn_sesumber_median=("nn_same", "median"),
)
summary["pct_vektor_identik"] = summary["n_vektor_identik"] / summary["n_dokumen"]
summary = summary.round(4)
summary.to_csv(OUT_CSV)

# Metadata eksekusi sesuai protokol bagian 18 butir 5
try:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                     stderr=subprocess.DEVNULL).strip()
except Exception:
    commit = None
with open(OUT_JSON, "w") as f:
    json.dump({
        "commit": commit,
        "waktu_utc": datetime.now(timezone.utc).isoformat(),
        "berkas_vektor": vec_paths[0],
        "total_vektor_identik": int(dup_mask.sum()),
        "per_source_type": summary.reset_index().to_dict(orient="records"),
    }, f, indent=2, ensure_ascii=False)

# Tampilan ringkasan di terminal
print("Total vektor identik:", int(dup_mask.sum()))
print(summary.to_string())
