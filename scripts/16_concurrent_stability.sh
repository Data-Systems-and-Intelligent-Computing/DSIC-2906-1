#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# DT-7 opsi C bagian B: dua salinan kueri identik dijalankan bersamaan oleh 4 proses,
# dengan timeout beku (700 ms, kontrol) dan batas latensi produksi paper (45 ms). Konfigurasi di parallel_benchmark.yaml.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
TANGGAL="$(date -u +%Y-%m-%d)"
for T in 700 45; do
  taskset -c 0-3 python -m src.benchmark.parallel_benchmark --mode stability --workers 4 --timeout-ms "$T" \
    --out "results/raw/concurrent_stability_t${T}_${TANGGAL}.jsonl"
done
