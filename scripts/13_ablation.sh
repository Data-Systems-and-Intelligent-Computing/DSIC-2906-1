#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# E5 / RQ5: ablasi n_sample, m_max, L_search pada workload DEVELOPMENT (README E5), bukan workload test.
# Grid konfigurasi ada di src/benchmark/dev_benchmark.py (configs()); hasil yang sama dipakai
# untuk memilih parameter beku dan timeout (DL-19).
PROFILE="${RESOURCE_PROFILE:-lightsail-t3.xlarge}"
TANGGAL="$(date -u +%Y-%m-%d)"
LOG="results/raw/dev_benchmark_${PROFILE}_${TANGGAL}.jsonl"
python -m src.benchmark.dev_benchmark --resource-profile "$PROFILE" --out "$LOG"
python -m src.evaluation.ablation --dev-log "$LOG" --out "results/summary/ablation_${PROFILE}_${TANGGAL}.csv"
