#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Benchmark utama predikat compound pada workload beku; menolak berjalan bila configs/main_benchmark.yaml belum frozen
PROFILE="${RESOURCE_PROFILE:-lightsail-t3.xlarge}"
TANGGAL="$(date -u +%Y-%m-%d)"
python -m src.benchmark.main_benchmark --types compound --resource-profile "$PROFILE" \
  --out "results/raw/main_compound_${PROFILE}_${TANGGAL}.jsonl"
