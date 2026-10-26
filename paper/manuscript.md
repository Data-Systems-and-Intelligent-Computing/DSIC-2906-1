# Metadata-Filtered Vector Search for Tourism Evidence

## Abstract
TBD after experiments; do not pre-fill performance claims.

## 1. Introduction
- Problem: metadata-filtered semantic retrieval over heterogeneous tourism evidence.
- Methodological anchor: Liu et al. (2026).
- Contribution: controlled transfer/adaptation study under natural, compound, and resource-constrained workloads.

## 2. Related Work
- Metadata-filtered vector search
- DiskANN / Filtered-DiskANN
- Predicate-agnostic graph search (ACORN, NaviX)
- Multi-index approaches (SIEVE, CAPS)

## 3. Method
- Corpus and natural metadata
- Exact filtered ground truth
- PostFilter, TwoHopSearch, AdaptiveL
- Resource profiles
- Workload and match-rate stratification

## 4. Experiments
- Recall@10–QPS
- p50/p95 latency
- search cost
- compound filters
- stability
- ablation

## 5. Results
TBD from frozen benchmark artifacts.

## 6. Discussion and Threats to Validity
### 6.x Threats to Validity

**Skala korpus.** Fakta: 64.354 dokumen vs indeks skala web WebIQ. Tidak ada klaim scalability; klaim difokuskan pada ketepatan dan perilaku terkontrol.

**Kekhususan domain.** Fakta: distribusi metadata JADESTA/berita berbeda dari YFCC/Caselaw/WebIQ di paper acuan.

**Keterwakilan kueri.** Fakta: kueri = 1.987 dokumen korpus yang ditahan (≥4 kata), bukan log pengguna; self-match dicegah.

**Distribusi filter.** Fakta: B5 hanya berisi predikat lebar, B1 tanpa predikat provinsi/kategori → perbandingan tunggal vs majemuk dibatasi ke B2–B3.

**Biaya ground truth eksak.** Fakta: kNN eksak layak karena korpus kecil (2.034 pasangan).

**Bias embedding dan asimetri teks.** Fakta: model dibekukan (MiniLM-L12-v2, 384 dimensi). Median panjang teks berita 74 karakter vs 133–152 JADESTA. Teks JADESTA bertemplat: cosine tetangga terdekat 0,92–0,93 vs 0,82 berita.

**Kualitas metadata.** Fakta: 16.340 perbaikan provinsi tercatat; 23% berita multi-kabupaten memakai any_match; robustness check: B4/B5 stabil, B2 bergeser ke rezim B1.

**Teks duplikat.** Fakta: 768 kelompok sindikasi; eksklusi kueri, vektor identik, dan story lineage yang sama.

**Emulasi sumber daya.** (diisi setelah benchmark di VM)

**Ketepatan implementasi.** Fakta: implementasi dicocokkan dengan Algorithm 1–3 paper; 29 unit test lulus; traversal graf di Python (QPS diberi label "implementasi Python").
## 7. Conclusion
