#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Development benchmark: hanya kueri dev (bukan workload test), untuk memilih parameter beku dan timeout (DL-19).
PROFILE="${RESOURCE_PROFILE:-lightsail-t3.xlarge-thread1}"
TANGGAL="$(date -u +%Y-%m-%d)"
python -m src.benchmark.dev_benchmark --resource-profile "$PROFILE" --out "results/raw/dev_benchmark_${PROFILE}_${TANGGAL}.jsonl"
