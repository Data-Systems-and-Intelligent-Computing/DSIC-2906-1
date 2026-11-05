#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# E6 / RQ4: kueri identik diulang dengan parameter beku, lalu overlap@k dihitung (README bagian 26).
# Menolak berjalan bila configs/main_benchmark.yaml belum frozen.
PROFILE="${RESOURCE_PROFILE:-lightsail-t3.xlarge}"
REPEATS="${REPEATS:-5}"
TANGGAL="$(date -u +%Y-%m-%d)"
LOG="results/raw/stability_${PROFILE}_${TANGGAL}.jsonl"
python -m src.benchmark.main_benchmark --types all --repeats "$REPEATS" --resource-profile "$PROFILE" --out "$LOG"
python -m src.benchmark.stability --log "$LOG" --out "results/summary/stability_${PROFILE}_${TANGGAL}.csv"
