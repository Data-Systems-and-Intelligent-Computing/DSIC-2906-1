#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Laporan Minggu 3: tabel utama (README 43) + pemecahan per query_in_filter dan sumber kueri,
# dari log benchmark utama di results/raw (tidak diubah). Argumen: tanggal run (YYYY-MM-DD).
PROFILE="${RESOURCE_PROFILE:-lightsail-t3.xlarge}"
TANGGAL="${1:?pakai: scripts/14_report.sh YYYY-MM-DD}"
LOGS=("results/raw/main_single_${PROFILE}_${TANGGAL}.jsonl" "results/raw/main_compound_${PROFILE}_${TANGGAL}.jsonl")
STAB="results/summary/stability_${PROFILE}_${TANGGAL}_per_pasangan.csv"
# DT-1: laporan dibuat terpisah untuk set utama dan set ekstensi
for SET in utama ekstensi; do
  OUT="results/summary/main_${PROFILE}_${TANGGAL}_${SET}"
  # Kolom stabilitas hanya digabung bila hasil 12_stability.sh untuk tanggal yang sama tersedia
  if [ -f "$STAB" ]; then
    python -m src.evaluation.report --log "${LOGS[@]}" --stability "$STAB" --set "$SET" --out-dir "$OUT"
  else
    python -m src.evaluation.report --log "${LOGS[@]}" --set "$SET" --out-dir "$OUT"
  fi
  # Grafik wajib naskah (README bagian 40) dari tabel yang baru dibuat
  python -m src.evaluation.plots --report-dir "$OUT" --out-dir "results/figures/main_${PROFILE}_${TANGGAL}_${SET}"
done
