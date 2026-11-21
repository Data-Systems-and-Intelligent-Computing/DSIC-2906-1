#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Konstruksi korpus (protokol bagian 16-17): kolom turunan, perbaikan provinsi (K-01), normalisasi penerbit,
# kelompok sindikasi, statistik panjang teks (T-03). Hasil: data/processed/corpus.parquet + manifest
python -m src.corpus.build_corpus "$@"
