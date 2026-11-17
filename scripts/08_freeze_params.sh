#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Pemeriksaan pembekuan sebelum benchmark utama (README bagian 42): config beku dan hash artefak cocok dengan manifest.
# Skrip ini hanya membaca; tidak mengubah berkas apa pun. Keluar dengan galat bila ada yang tidak cocok.
python - <<'PY'
import hashlib, json, sys
from pathlib import Path
import pandas as pd
import yaml

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

gagal = []
# Config yang wajib beku
for c in ["configs/main_benchmark.yaml", "configs/resource_profiles.yaml", "configs/parallel_benchmark.yaml"]:
    beku = yaml.safe_load(Path(c).read_text(encoding="utf-8")).get("frozen") is True
    print(f"{'OK ' if beku else 'GAGAL'} {c} frozen={beku}")
    gagal += [] if beku else [c]
# Artefak beku dibandingkan dengan manifest
cek = [("data/processed/workload.parquet", pd.read_csv("data/manifests/workload_manifest.csv").iloc[0]["checksum_sha256"]),
       ("data/groundtruth/filtered_knn_k10.parquet", pd.read_csv("data/manifests/groundtruth_manifest.csv").iloc[0]["checksum_sha256"])]
for path, harap in cek:
    cocok = Path(path).exists() and sha(path) == harap
    print(f"{'OK ' if cocok else 'GAGAL'} {path}")
    gagal += [] if cocok else [path]
sys.exit(1 if gagal else 0)
PY
