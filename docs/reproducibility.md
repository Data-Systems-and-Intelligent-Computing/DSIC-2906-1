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
`python -m src.embedding.embed` (atau `scripts/02_embed.sh`)
Model paraphrase-multilingual-MiniLM-L12-v2, 384 dimensi. Hash vektor dasar:
9000996250c758426772d98ad2e3e634e6b1de9af47da66965e13156f5b9f320 (data/manifests/vector_manifest.csv).

## 5. Indeks DiskANN
`python -m src.index.build_diskann` (atau `scripts/06_build_index.sh`), dijalankan di lingkungan Docker berisi diskannpy 0.7.0 (Linux x86_64)
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
scripts/11_resource_benchmark.sh      # profil core RC-small/RC-medium/RC-reference (configs/resource_profiles.yaml)
```
Lingkungan run acuan: OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1, PYTHONUNBUFFERED=1,
RESOURCE_PROFILE=lightsail-t3.xlarge-thread1. Skrip 11 dijalankan setelah 09, 10, dan 12 selesai (tidak bersamaan).

Run acuan 15 Nov 2026 UTC (commit ddf690c untuk 09/10/12, commit 072ac39 untuk 11), SHA-256 log mentah:
```
aa866c3620d2c341debb37b96d90e1898f53d33598e2f6d820c38db778d39e7e  main_single_lightsail-t3.xlarge-thread1_2026-11-15.jsonl     (13.644 baris)
9e7bb46d05a9f7d90485982e0cd141cec748475a5ae9ea4867b2e95d1df126e8  main_compound_lightsail-t3.xlarge-thread1_2026-11-15.jsonl   (10.836 baris)
de051b05cf676000ea7fab7165d5c931e922aee4d99e99c1bb5557d94215d678  stability_lightsail-t3.xlarge-thread1_2026-11-15.jsonl       (122.400 baris)
eced6e9e7b22221ca7d17967b352d6b120c38145dfa1b9e37883e86922804505  resource_RC-small_2026-11-15.jsonl                           (24.480 baris)
e579bbb54917e78a5fb645b9d039d4a8ed753799fa2dc2a101d7815351b9f90d  resource_RC-medium_2026-11-15.jsonl                          (24.480 baris)
cff9e2e3a8c62d5c313d1e063bb2ac5d499d6b1443c7d91028e09c4c7699922c  resource_RC-reference_2026-11-15.jsonl                       (24.480 baris)
```
Log mentah tidak masuk git (results/raw di-.gitignore); salinannya disimpan di luar repo.
Runner menolak berjalan bila parameter belum beku, dan memeriksa hash workload terhadap manifest.
Setiap baris log mencatat commit, workload_id, hash workload dan ground truth, profil, dan jumlah thread.

## 9. Tabel dan grafik
```
scripts/14_report.sh <tanggal-run>
```
Ringkasan stabilitas dibuat oleh skrip 12; bila dihitung ulang:
python -m src.benchmark.stability --log results/raw/stability_<profil>_<tanggal>.jsonl --out results/summary/stability_<profil>_<tanggal>.csv

Hasil, dipisah per set (DT-1): results/summary/main_<profil>_<tanggal>_{utama,ekstensi}/
(main_table, per_match_rate, per_query_in_filter, per_sumber_kueri, failure_taxonomy, _meta.json berisi SHA-256 log sumber)
dan results/figures/main_<profil>_<tanggal>_{utama,ekstensi}/ (PNG).

Tabel statistik korpus (README bagian 40 item 1):
python -m src.evaluation.corpus_table --out-dir results/summary/corpus_2026-11-15

Uji reproduksi (README bagian 47): menjalankan ulang 14_report.sh dari log mentah acuan menghasilkan
main_table.csv yang identik dengan versi ter-commit (git diff kosong pada folder _utama dan _ekstensi).

## 10. Pengujian
```
python -m pytest -q
```
Log uji yang dilampirkan di naskah: results/summary/pytest_2026-11-16.txt (67 lulus).