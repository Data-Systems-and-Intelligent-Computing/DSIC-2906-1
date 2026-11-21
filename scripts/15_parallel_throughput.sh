#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Draf P5: QPS dengan kueri paralel per profil core (W proses = jumlah core, dibatasi taskset).
# Profil di configs/parallel_benchmark.yaml (beku). Tiap pekerja satu thread pustaka numerik.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
TANGGAL="$(date -u +%Y-%m-%d)"
for P in "RC-small 0 1" "RC-medium 0-1 2" "RC-reference 0-3 4"; do
  set -- $P
  taskset -c "$2" python -m src.benchmark.parallel_benchmark --mode throughput --workers "$3" --profile "$1" \
    --out "results/raw/parallel_${1}_${TANGGAL}.jsonl"
done
