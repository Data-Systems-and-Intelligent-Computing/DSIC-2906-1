#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Workload beku (protokol bagian 18): populasi predikat, syarat kecukupan >= 10 x k (set utama) dan >= k (set ekstensi, DT-1),
# bin match rate, kueri dengan pengecualian self-match, seed dari configs/workload.yaml.
# Hasil: data/processed/{filters,queries,workload}.parquet + data/manifests/workload_manifest.csv
python -m src.workload.build_queries "$@"
