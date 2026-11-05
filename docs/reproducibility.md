# Reproducibility

Panduan mereproduksi seluruh hasil DSIC-2906-1 dari berkas mentah sampai tabel dan grafik.
Setiap tahap menulis manifest berisi SHA-256; hasil reproduksi sah bila hash cocok.
Semua perintah dijalankan dari root repo dengan virtualenv aktif.

## 0. Lingkungan
- Python 3.12; daftar paket server: results/summary/env_lightsail_2026-10-29.txt (dibuat dengan uv).
- Mesin benchmark: AWS Lightsail t3.xlarge (4 vCPU burstable, 16 GB, mesin bersama), Ubuntu 24.04.
- Indeks dibangun dengan diskannpy 0.7.0 (Linux x86_64, Python 3.11), lihat data/manifests/index_manifest.json.
- Semua benchmark resmi dijalankan dengan satu thread:
  `export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`

## 1. Berkas mentah (tidak di-commit; tersedia di bucket sigerciv1-dsic-2906-1-data)
- data/raw/jadesta/*.csv: berkas JADESTA asli, identik dengan data/_asli/data-jadesta/.
- data/raw/news/*.csv: berkas berita asli (kolom Provinsi kosong).
- Hash: data/manifests/jadesta_sha256.csv dan data/manifests/bucket_sha256.csv.
- Versi yang dimodifikasi Antigravity untuk workload v1 diarsipkan di data/_v1_antigravity/
  dan tidak dipakai lagi (docs/provinsi-k01.md).

## 2. Tabel referensi kabupaten -> provinsi
```
python scripts/build_reference_kabprov.py --pdf "<Lampiran Kepmendagri 300.2.2-2138 Tahun 2025>.pdf" --out-dir data/reference
```
Sumber, tanggal unduh, dan SHA-256 PDF: data/reference/SOURCE.md. Alias ejaan: data/reference/kabupaten_alias.csv.
Validasi: 38 provinsi, 416 kabupaten, 98 kota.

## 3. Korpus
```
python -m src.corpus.build_corpus
```
Hasil: data/processed/corpus.parquet. Cocokkan snapshot_id dengan data/manifests/source_manifest.csv (snap-18898d4ada35)
dan ringkasan dengan data/processed/corpus_summary.json (64.354 dokumen).

## 4. Embedding
[Cek perintah di scripts/02_embed.sh]
Model paraphrase-multilingual-MiniLM-L12-v2, 384 dimensi. Hash vektor dasar:
9000996250c758426772d98ad2e3e634e6b1de9af47da66965e13156f5b9f320 (data/manifests/vector_manifest.csv).

## 5. Indeks DiskANN
[Cek perintah di scripts/06_build_index.sh; indeks dibangun lewat Docker]
Parameter dan hash berkas indeks: data/manifests/index_manifest.json (R = 64, L_build = 100).
Sanity: recall@10 tanpa filter 0,9959.

## 6. Workload dan ground truth (beku, v2)
```
python -m src.workload.build_queries
python -m src.groundtruth.build_groundtruth
```
Konfigurasi: configs/workload.yaml (seed 2906). Hash yang harus cocok:
- workload.parquet: b5d7d6f8c48155db84a26927ef717d521e0e44fef98c5307f0cadb50ca67c520 (data/manifests/workload_manifest.csv)
- filtered_knn_k10.parquet: 2e116d0002229a4f07b9e462126951aa82fd34a575afb54d28dc08b1d935ec58 (data/manifests/groundtruth_manifest.csv)

## 7. Development benchmark dan pembekuan parameter
```
python -m src.benchmark.dev_benchmark --resource-profile lightsail-t3.xlarge-thread1 \
  --out results/raw/dev_benchmark_lightsail_thread1_<tanggal>.jsonl
python -m src.evaluation.ablation --dev-log results/raw/dev_benchmark_lightsail_thread1_<tanggal>.jsonl \
  --out results/summary/<folder>/ablation_adaptivel.csv
```
Run acuan 5 Nov 2026 (commit d20b04a): SHA-256 JSONL
9f63eeb88fa4623a69e21ee6dabcbb50ef2187195ea604e43ae61c4d77e248a8 (results/summary/dev_lightsail_thread1_2026-11-05/_meta.json).
Parameter beku dan timeout: configs/main_benchmark.yaml (berlaku hanya bila frozen: true).

## 8. Benchmark utama, stabilitas, dan profil sumber daya
```
scripts/09_main_single_filters.sh
scripts/10_main_compound_filters.sh
REPEATS=5 scripts/12_stability.sh
scripts/11_resource_benchmark.sh      # menunggu keputusan DT-6
```
Runner menolak berjalan bila parameter belum beku, dan memeriksa hash workload terhadap manifest.
Setiap baris log mencatat commit, workload_id, hash workload dan ground truth, profil, dan jumlah thread.

## 9. Tabel dan grafik
```
scripts/14_report.sh <tanggal-run>
```
Hasil: results/summary/main_<profil>_<tanggal>/ (CSV + _meta.json berisi SHA-256 log sumber)
dan results/figures/main_<profil>_<tanggal>/ (PNG dan SVG).

## 10. Pengujian
```
python -m pytest -q
```
Log uji yang dilampirkan di naskah: results/summary/pytest_2026-11-05.txt.