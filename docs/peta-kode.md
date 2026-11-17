# Peta kode DSIC-2906-1

Peta ini menunjukkan skrip, modul, keluaran, dan tes untuk setiap tahap pipeline.
Semua perintah dijalankan dari root repo dengan virtualenv aktif. `make <target>` memanggil skrip yang sama.

## Pipeline utama (skrip 00-14)

| No | Tahap (README) | Skrip / make | Modul utama | Keluaran utama | Tes |
|---|---|---|---|---|---|
| 00 | E0 audit korpus mentah | `00_audit_corpus.sh` / `make audit` | `src/corpus/audit.py` | ringkasan audit (layar) | – |
| 01 | Konstruksi korpus (protokol 16-17) | `01_build_corpus.sh` / `make corpus` | `src/corpus/build_corpus.py`, `publishers.py`, `province_map.py` | `data/processed/corpus.parquet`, `normalization_report.csv`, `corpus_summary.json` | `test_corpus_build.py` |
| 02 | Embedding (README 12) | `02_embed.sh` / `make embed` | `src/embedding/embed.py` | `data/embeddings/base_vectors.npy`, `vector_manifest.csv` | – |
| 03 | Workload + filter (protokol 18) | `03_build_queries.sh` / `make queries` | `src/workload/build_queries.py`, `build_filters.py`, `stratify_match_rate.py` | `data/processed/{filters,queries,workload}.parquet`, `workload_manifest.csv` | `test_workload_build.py`, `test_workload_freeze.py`, `test_predicates.py` |
| 04 | Pemeriksaan filter | `04_build_filters.sh` / `make filters` | (keluaran 03) | ringkasan predikat (layar) | – |
| 05 | Ground truth eksak G0 (README 17) | `05_groundtruth.sh` / `make groundtruth` | `src/groundtruth/build_groundtruth.py`, `exact_filtered_knn.py` | `data/groundtruth/filtered_knn_k10.parquet` | `test_exact_groundtruth.py` |
| 06 | Indeks DiskANN (README 20) | `06_build_index.sh` / `make index` | `src/index/build_diskann.py`, `index_manifest.py` | `index/diskann/tourism*`, `index_manifest.json` | `scripts/tools/check_diskann.py` |
| 07 | Development benchmark | `07_dev_benchmark.sh` / `make dev` | `src/benchmark/dev_benchmark.py` | `results/raw/dev_benchmark_*.jsonl` | `test_dev_exclusion.py` |
| 08 | Pemeriksaan pembekuan (README 42) | `08_freeze_params.sh` / `make freeze` | (skrip di dalam berkas) | OK/GAGAL per config dan hash | – |
| 09 | E2 predikat tunggal | `09_main_single_filters.sh` / `make single` | `src/benchmark/main_benchmark.py` | `results/raw/main_single_*.jsonl` | `test_main_benchmark.py`, `test_timeout.py` |
| 10 | E3 predikat majemuk | `10_main_compound_filters.sh` / `make compound` | `src/benchmark/main_benchmark.py` | `results/raw/main_compound_*.jsonl` | (sama dengan 09) |
| 11 | E4 profil core | `11_resource_benchmark.sh` / `make resource` | `main_benchmark.py` + `taskset` | `results/raw/resource_RC-*.jsonl`, `results/summary/resource_*.csv` | – |
| 12 | E6 stabilitas | `12_stability.sh` / `make stability` | `main_benchmark.py --repeats`, `src/benchmark/stability.py` | `results/raw/stability_*.jsonl`, `results/summary/stability_*.csv` | `test_stability.py` |
| 13 | E5 ablasi AdaptiveL (dev) | `13_ablation.sh` / `make ablation` | `dev_benchmark.py`, `src/evaluation/ablation.py` | `results/summary/ablation_*.csv` | `test_ablation.py` |
| 14 | Tabel dan grafik (README 40, 43) | `14_report.sh <tanggal>` / `make report TANGGAL=<tanggal>` | `src/evaluation/report.py`, `plots.py`, `failure_analysis.py`, `bootstrap.py`, `latency.py` | `results/summary/main_*_{utama,ekstensi}/`, `results/figures/main_*_{utama,ekstensi}/` | `test_report.py`, `test_plots.py`, `test_failure_analysis.py` |
| 15 | Draf P5: QPS kueri paralel per profil core | `15_parallel_throughput.sh` / `make parallel` | `src/benchmark/parallel_benchmark.py` | `results/raw/parallel_RC-*.jsonl` + `_ringkas.csv` | `test_parallel_benchmark.py` |
| 16 | DT-7: stabilitas konkuren + timeout (700 / 45 ms) | `16_concurrent_stability.sh` / `make concurrent` | `src/benchmark/parallel_benchmark.py` | `results/raw/concurrent_stability_t*.jsonl` + `_ringkas.csv` | `test_parallel_benchmark.py` |

Robustness DT-3 (draf pembimbing DT-3 opsi C dan P7): `python -m src.evaluation.robustness_dt3 --main-log <main_single> <main_compound> --out-log results/raw/robustness_dt3_<tanggal>.jsonl --out-dir results/summary/robustness_dt3_<tanggal>` (tes: `test_robustness_dt3.py`).

Tabel statistik korpus (README 40 item 1): `python -m src.evaluation.corpus_table --out-dir results/summary/corpus_<tanggal>`.

## Metode pencarian (dipakai 07, 09-13)

| Metode | Modul | Acuan | Tes |
|---|---|---|---|
| Penelusuran greedy, frontier, timeout | `src/search/graph_index.py` | DiskANN graph (Vamana) | `test_graph_search.py` |
| B0 PostFilter | `src/search/postfilter.py` | README 18 | `test_postfilter.py` |
| B1 TwoHopSearch | `src/search/twohop.py` | Liu et al. Algorithm 1 | `test_twohop.py` |
| P1 AdaptiveL | `src/search/adaptivel.py` | Liu et al. Algorithms 2-3 | `test_adaptivel.py` |

Format log run: `src/benchmark/runner.py` (REQUIRED_LOG_FIELDS), ditulis oleh `src/benchmark/logger.py`.

## Alat bantu (bukan bagian pipeline 00-14)

Alat di `src/tools/` menulis berkas dan menolak jalan bila diimpor; jalankan langsung dengan `python src/tools/<nama>.py`.

| Alat | Kegunaan |
|---|---|
| `scripts/tools/build_reference_kabprov.py` | Tabel referensi kab/kota → provinsi dari Kepmendagri 2025 (K-01) |
| `scripts/tools/province_derive.py` | Penurunan provinsi dan laporan selisih terhadap workload v1 (K-01) |
| `scripts/tools/check_diskann.py` | Uji cepat bahwa diskannpy terpasang (data acak) |
| `scripts/tools/check_unfiltered_recall.py` | E1: recall@10 tanpa filter penelusuran Python vs diskannpy |
| `scripts/tools/ringkasan_bimbingan.py` | Angka utama progres untuk bimbingan (hanya membaca) |
| `src/tools/province_diff.py`, `merge_province_report.py`, `add_original_hash.py` | Asal-usul perapian provinsi (K-01) |
| `src/tools/template_effect.py` | Efek templat teks JADESTA pada embedding (ancaman validitas) |
| `src/tools/report_bins.py` | Median dan rentang match rate per bin (gate protokol 21) |

## Konfigurasi

| Berkas | Status | Dibaca oleh |
|---|---|---|
| `configs/main_benchmark.yaml` | beku | `main_benchmark.py` (grid metode, timeout, k) |
| `configs/resource_profiles.yaml` | beku | dokumentasi skrip 11 |
| `configs/workload.yaml` | beku (26 Okt) | `build_queries.py`, `main_benchmark.py` |
| `configs/embedding.yaml`, `configs/diskann.yaml` | dikunci | `embed.py`, `build_diskann.py` |
| `configs/corpus.yaml`, `experiment.yaml`, `search.yaml`, `metadata.yaml` | dokumentasi setup aktual | tidak dibaca kode |

## Pemeriksaan rutin

```
python -m pytest -q                 # semua tes harus lulus
bash scripts/08_freeze_params.sh    # semua baris harus OK
```
