#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# E4 / RQ3: workload beku yang sama dijalankan ulang pada beberapa profil core CPU.
# CPU dibatasi dengan taskset dan jumlah thread pustaka numerik disamakan dengan jumlah core;
# memori tidak dibatasi (tidak ada akses cgroup), puncak RSS diukur (naskah 4.4).
# Profil ditetapkan di configs/resource_profiles.yaml sebelum hasil benchmark utama dilihat.
# Runner menolak berjalan bila configs/main_benchmark.yaml belum frozen.
TANGGAL="$(date -u +%Y-%m-%d)"
mkdir -p results/summary
RINGKAS="results/summary/resource_${TANGGAL}.csv"
echo "profile,cores,threads,wall_s,user_s,sys_s,peak_rss_mb" > "$RINGKAS"

# Format tiap profil: nama, daftar core untuk taskset, jumlah thread
for P in "RC-small 0 1" "RC-medium 0-1 2" "RC-reference 0-3 4"; do
  set -- $P
  NAMA="$1"; CORES="$2"; THREADS="$3"
  export OMP_NUM_THREADS="$THREADS" OPENBLAS_NUM_THREADS="$THREADS" MKL_NUM_THREADS="$THREADS"
  OUT="results/raw/resource_${NAMA}_${TANGGAL}.jsonl"

  # Benchmark dijalankan sebagai proses anak; getrusage(RUSAGE_CHILDREN) memberi waktu CPU dan puncak RSS-nya.
  # Output benchmark diarahkan ke stderr supaya tidak tercampur dengan baris ringkasan CSV.
  python - "$NAMA" "$CORES" "$THREADS" "$OUT" >> "$RINGKAS" <<'PY'
import resource, subprocess, sys, time
nama, cores, threads, out = sys.argv[1:]
t0 = time.time()
subprocess.run(["taskset", "-c", cores, sys.executable, "-m", "src.benchmark.main_benchmark",
                "--types", "all", "--resource-profile", nama, "--out", out],
               check=True, stdout=sys.stderr)
r = resource.getrusage(resource.RUSAGE_CHILDREN)
# ru_maxrss di Linux bersatuan KB
print(f"{nama},{cores},{threads},{time.time() - t0:.1f},{r.ru_utime:.1f},{r.ru_stime:.1f},{r.ru_maxrss / 1024:.1f}")
PY
  echo "selesai: $NAMA -> $OUT"
done
