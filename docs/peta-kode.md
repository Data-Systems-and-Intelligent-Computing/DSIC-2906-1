# Code map for DSIC-2906-1

This map shows which script, module, output, and test belong to each pipeline stage.
Run every command from the repo root with the virtualenv active. `make <target>` calls the same script.

## Main pipeline (scripts 00-14)

| No | Stage (README) | Script / make | Main module | Main output | Test |
|---|---|---|---|---|---|
| 00 | E0 raw corpus audit | `00_audit_corpus.sh` / `make audit` | `src/corpus/audit.py` | audit summary (stdout) | – |
| 01 | Corpus construction (protocol 16-17) | `01_build_corpus.sh` / `make corpus` | `src/corpus/build_corpus.py`, `publishers.py`, `province_map.py` | `data/processed/corpus.parquet`, `normalization_report.csv`, `corpus_summary.json` | `test_corpus_build.py` |
| 02 | Embedding (README 12) | `02_embed.sh` / `make embed` | `src/embedding/embed.py` | `data/embeddings/base_vectors.npy`, `vector_manifest.csv` | – |
| 03 | Workload + filters (protocol 18) | `03_build_queries.sh` / `make queries` | `src/workload/build_queries.py`, `build_filters.py`, `stratify_match_rate.py` | `data/processed/{filters,queries,workload}.parquet`, `workload_manifest.csv` | `test_workload_build.py`, `test_workload_freeze.py`, `test_predicates.py` |
| 04 | Filter check | `04_build_filters.sh` / `make filters` | (output of 03) | predicate summary (stdout) | – |
| 05 | Exact ground truth G0 (README 17) | `05_groundtruth.sh` / `make groundtruth` | `src/groundtruth/build_groundtruth.py`, `exact_filtered_knn.py` | `data/groundtruth/filtered_knn_k10.parquet` | `test_exact_groundtruth.py` |
| 06 | DiskANN index (README 20) | `06_build_index.sh` / `make index` | `src/index/build_diskann.py`, `index_manifest.py` | `index/diskann/tourism*`, `index_manifest.json` | `scripts/tools/check_diskann.py` |
| 07 | Development benchmark | `07_dev_benchmark.sh` / `make dev` | `src/benchmark/dev_benchmark.py` | `results/raw/dev_benchmark_*.jsonl` | `test_dev_exclusion.py` |
| 08 | Freeze check (README 42) | `08_freeze_params.sh` / `make freeze` | (inline script) | OK/FAIL per config and hash | – |
| 09 | E2 single predicates | `09_main_single_filters.sh` / `make single` | `src/benchmark/main_benchmark.py` | `results/raw/main_single_*.jsonl` | `test_main_benchmark.py`, `test_timeout.py` |
| 10 | E3 compound predicates | `10_main_compound_filters.sh` / `make compound` | `src/benchmark/main_benchmark.py` | `results/raw/main_compound_*.jsonl` | (same as 09) |
| 11 | E4 core profiles | `11_resource_benchmark.sh` / `make resource` | `main_benchmark.py` + `taskset` | `results/raw/resource_RC-*.jsonl`, `results/summary/resource_*.csv` | – |
| 12 | E6 stability | `12_stability.sh` / `make stability` | `main_benchmark.py --repeats`, `src/benchmark/stability.py` | `results/raw/stability_*.jsonl`, `results/summary/stability_*.csv` | `test_stability.py` |
| 13 | E5 AdaptiveL ablation (dev) | `13_ablation.sh` / `make ablation` | `dev_benchmark.py`, `src/evaluation/ablation.py` | `results/summary/ablation_*.csv` | `test_ablation.py` |
| 14 | Tables and figures (README 40, 43) | `14_report.sh <date>` / `make report TANGGAL=<date>` | `src/evaluation/report.py`, `plots.py`, `failure_analysis.py`, `bootstrap.py`, `latency.py` | `results/summary/main_*_{utama,ekstensi}/`, `results/figures/main_*_{utama,ekstensi}/` | `test_report.py`, `test_plots.py`, `test_failure_analysis.py` |

Corpus statistics table (README 40 item 1): `python -m src.evaluation.corpus_table --out-dir results/summary/corpus_<date>`.

## Search methods (shared by 07, 09-13)

| Method | Module | Reference | Test |
|---|---|---|---|
| Greedy traversal, beam, timeout | `src/search/graph_index.py` | DiskANN graph (Vamana) | `test_graph_search.py` |
| B0 PostFilter | `src/search/postfilter.py` | README 18 | `test_postfilter.py` |
| B1 TwoHopSearch | `src/search/twohop.py` | Liu et al. Algorithm 1 | `test_twohop.py` |
| P1 AdaptiveL | `src/search/adaptivel.py` | Liu et al. Algorithms 2-3 | `test_adaptivel.py` |

Run log format: `src/benchmark/runner.py` (REQUIRED_LOG_FIELDS), written by `src/benchmark/logger.py`.

## Helper tools (not part of the 00-14 pipeline)

The tools in `src/tools/` write files and refuse to run when imported; run them directly with `python src/tools/<name>.py`.

| Tool | Purpose |
|---|---|
| `scripts/tools/build_reference_kabprov.py` | Kab/kota → province reference table from Kepmendagri 2025 (K-01) |
| `scripts/tools/province_derive.py` | Province derivation and diff report against workload v1 (K-01) |
| `scripts/tools/check_diskann.py` | Quick check that diskannpy is installed (random data) |
| `scripts/tools/ringkasan_bimbingan.py` | Key progress numbers for supervision meetings (read-only) |
| `src/tools/province_diff.py`, `merge_province_report.py`, `add_original_hash.py` | Provenance of the province cleanup (K-01) |
| `src/tools/template_effect.py` | Effect of the JADESTA text template on embeddings (threat to validity) |
| `src/tools/report_bins.py` | Median and range of match rate per bin (protocol 21 gate) |

## Configuration

| File | Status | Read by |
|---|---|---|
| `configs/main_benchmark.yaml` | frozen | `main_benchmark.py` (method grid, timeout, k) |
| `configs/resource_profiles.yaml` | frozen | documentation for script 11 |
| `configs/workload.yaml` | frozen (26 Oct) | `build_queries.py`, `main_benchmark.py` |
| `configs/embedding.yaml`, `configs/diskann.yaml` | fixed | `embed.py`, `build_diskann.py` |
| `configs/corpus.yaml`, `experiment.yaml`, `search.yaml`, `metadata.yaml` | documentation of the actual setup | not read by code |

## Routine checks

```
python -m pytest -q                 # all tests must pass
bash scripts/08_freeze_params.sh    # every line must be OK
```
