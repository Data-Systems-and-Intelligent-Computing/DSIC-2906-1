#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Ground truth eksak G0 (protokol bagian 19 butir 1): pencarian menyeluruh pada dokumen yang lolos filter,
# setelah pengecualian self-match. Hasil: data/groundtruth/filtered_knn_k10.parquet + groundtruth_manifest.csv
python -m src.groundtruth.build_groundtruth "$@"
