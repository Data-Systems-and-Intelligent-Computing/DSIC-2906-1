#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# E0: audit berkas mentah (jumlah dokumen, kardinalitas metadata, kerusakan kolom provinsi, konsentrasi penerbit)
python -m src.corpus.audit "$@"
