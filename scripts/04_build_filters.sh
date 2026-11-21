#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Predikat alami tunggal dan majemuk dibuat bersama workload oleh 03_build_queries.sh (data/processed/filters.parquet).
# Skrip ini hanya memeriksa bahwa berkas filter tersedia dan menampilkan ringkasannya.
python - <<'PY'
import pandas as pd
f = pd.read_parquet("data/processed/filters.parquet")
print(len(f), "predikat"); print(f.columns.tolist())
PY
