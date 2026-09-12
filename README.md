# DSIC-2906 — Metadata-Filtered Vector Search for Tourism Evidence

Repository penelitian untuk adaptasi terkontrol metode **AdaptiveL** dari paper:

> Fang Liu et al. (Microsoft), **Metadata-Filtered Vector Search in the WebIQ Grounding Index**, VLDB 2026 Workshop: The 2nd Workshop on Vector Databases.

Judul Indonesia yang direkomendasikan:

> **Pencarian Vektor Berfilter Metadata untuk Evidence Pariwisata: Evaluasi AdaptiveL pada Predikat Alami, Majemuk, dan Sumber Daya Terbatas**

Judul artikel bahasa Inggris yang direkomendasikan:

> **Metadata-Filtered Vector Search for Tourism Evidence: Evaluating AdaptiveL under Natural, Compound, and Resource-Constrained Workloads**

Alternatif yang lebih problem-driven:

> **Does AdaptiveL Transfer to Resource-Constrained Tourism Evidence Search? A Controlled Evaluation under Natural and Compound Metadata Filters**

---

## 1. Keputusan Perubahan Arah Penelitian

Penelitian ini **tidak lagi berfokus pada Direct/Verify/Abstain atau conflict-aware query handling**.

Objek ilmiah baru adalah:

```text
metadata-filtered approximate nearest-neighbor search
```

Fokus utama adalah menguji apakah prinsip **predicate-agnostic, selectivity-adaptive graph search** yang digunakan oleh AdaptiveL tetap efektif ketika dipindahkan dari grounding web berskala sangat besar ke corpus evidence pariwisata yang:

- lebih kecil;
- heterogen;
- mempunyai metadata wilayah, kategori, sumber, dan waktu;
- menggunakan predikat tunggal maupun majemuk;
- dijalankan pada sumber daya komputasi terbatas.

Paper Liu et al. menjadi **acuan metodologis utama**, bukan sekadar related work.

---

## 2. Kalimat Jangkar Penelitian

> Penelitian ini mengevaluasi transferabilitas AdaptiveL untuk metadata-filtered vector search pada corpus evidence pariwisata dengan menguji recall, throughput, latency, stability, dan resource cost pada berbagai regime filter match rate, tipe metadata predicate, dan resource cap menggunakan satu shared proximity graph yang sama.

---

## 3. Publication Boundary

Penelitian ini memiliki boundary berikut:

> **DSIC-2906 owns the controlled adaptation and evaluation of selectivity-adaptive, predicate-agnostic vector search for heterogeneous tourism evidence under natural, compound, and resource-constrained metadata-filter workloads.**

Penelitian ini **tidak** mengklaim kontribusi utama pada:

- model embedding baru;
- semantic reranker baru;
- RAG;
- generative QA;
- hallucination detection;
- truth discovery;
- source reliability learning;
- evidence fusion;
- knowledge graph reasoning;
- LLM-based query rewriting;
- crawler sebagai novelty;
- MinIO, Iceberg, Spark, atau Trino sebagai novelty;
- graph index baru yang menggantikan DiskANN.

Kontribusi harus tetap berada pada **filtered vector retrieval behavior dan trade-off sistemnya**.

---

## 4. Paper Acuan Utama dan Bagian yang Diadaptasi

Paper acuan menggunakan DiskANN sebagai graph-based vector index dan mengembangkan filtered search yang:

1. bekerja pada **single shared vector index**;
2. bersifat **predicate-agnostic**, sehingga index tidak perlu dibangun ulang untuk setiap metadata predicate;
3. mengestimasi **filter specificity / match rate** selama pencarian;
4. memperbesar search frontier ketika predicate sangat selektif;
5. mengevaluasi trade-off **recall–QPS**;
6. mengevaluasi **result stability** selain accuracy dan latency.

Elemen yang diadaptasi langsung:

```text
single shared proximity graph
predicate-aware evaluation at query time
filter match-rate regimes
TwoHopSearch baseline
AdaptiveL search
recall@k vs QPS
repeated-query stability
```

Elemen yang diubah untuk DSIC-2906:

```text
Web corpus       -> tourism evidence corpus
site/time filter -> region/category/source/time/compound filters
web-scale        -> resource-constrained deployment
single filters   -> natural single + compound predicates
production ICG   -> exact filtered kNN recall + optional relevance audit
```

Penelitian ini harus menyebut dirinya sebagai **adaptation / external evaluation / systems study**, kecuali final literature review mendukung klaim kebaruan yang lebih kuat.

---

## 5. Research Gap yang Aman

Paper acuan menunjukkan AdaptiveL pada dataset publik dan WebIQ production-scale. DSIC-2906 tidak boleh mengklaim bahwa belum pernah ada penelitian filtered vector search untuk domain lain tanpa verifikasi literatur.

Gap yang dapat diuji langsung dari desain penelitian ini adalah:

> **Apakah keuntungan AdaptiveL terhadap baseline tetap bertahan ketika workload dipindahkan ke heterogeneous tourism evidence, menggunakan natural dan compound metadata predicates, serta dijalankan di bawah resource cap yang jauh lebih ketat daripada lingkungan WebIQ?**

Ini adalah **empirical systems question**.

Klaim seperti:

```text
first tourism filtered vector search
first resource-constrained AdaptiveL
first compound-filter evaluation
```

**dilarang** sampai literature search final mendukungnya.

---

## 6. Research Questions

### RQ1 — Utama

**Does AdaptiveL improve the recall–throughput trade-off over naive post-filtering and TwoHopSearch for metadata-filtered vector retrieval on heterogeneous tourism evidence across different filter match-rate regimes?**

### RQ2 — Predicate Complexity

**How does AdaptiveL behave under natural single predicates compared with compound predicates combining region, category, source, and temporal metadata?**

### RQ3 — Resource Constraint

**How sensitive are AdaptiveL's recall, latency, throughput, and search cost to fixed CPU and memory limits in a resource-constrained deployment?**

### RQ4 — Stability

**Does AdaptiveL produce more stable top-k result sets than TwoHopSearch and post-filtering when identical filtered queries are repeated under the same frozen index and resource configuration?**

### RQ5 — Parameter Sensitivity

**How do `L_search`, `n_sample`, and maximum AdaptiveL multiplier affect recall, QPS, latency, visited nodes, and predicate-evaluation cost across low- and high-match-rate queries?**

RQ1–RQ4 adalah core article.

RQ5 adalah ablation/secondary analysis.

---

## 7. Hipotesis

### H1 — Low Match-Rate Advantage

AdaptiveL diperkirakan mempunyai recall lebih tinggi daripada TwoHopSearch dan naive post-filtering pada filter dengan match rate rendah, pada search budget yang sebanding.

### H2 — Throughput Trade-off

Untuk target recall yang sama, AdaptiveL diperkirakan membutuhkan search effort yang lebih efisien daripada TwoHopSearch pada selective predicates.

### H3 — Compound Predicate Robustness

Keuntungan AdaptiveL diperkirakan tetap terlihat pada compound predicates selama jumlah eligible points masih cukup untuk membentuk top-k ground truth.

### H4 — Stability

AdaptiveL diperkirakan mempunyai repeated-query result overlap yang lebih tinggi daripada TwoHopSearch pada highly selective filters.

### H5 — Resource Sensitivity

Resource cap yang lebih ketat diperkirakan memperbesar trade-off antara recall dan latency/QPS, terutama pada low-match-rate predicates yang memerlukan frontier expansion lebih besar.

Semua hipotesis boleh ditolak.

---

## 8. Scientific Unit of Analysis

Unit utama:

```text
query × metadata predicate × search method × resource profile
```

Unit statistik utama:

```text
query-filter pair
```

Satu query dapat diuji pada seluruh metode agar comparison bersifat paired.

---

## 9. Data Sources

### D1 — JADESTA

Peran utama:

```text
structured tourism corpus + natural metadata
```

Gunakan seluruh snapshot JADESTA yang tersedia, bukan hanya entity yang konflik.

Field yang berpotensi menjadi metadata filter:

- province;
- regency/city;
- district bila tersedia;
- tourism category/type;
- entity identifier;
- source type;
- crawl/snapshot time.

Text yang di-embed hanya field yang memang mengandung content semantik, misalnya:

```text
name + description + attraction/package text
```

Jangan memasukkan metadata filter secara berlebihan ke text hanya untuk mempermudah vector similarity.

### D2 — Wikipedia Tourism Content

Peran:

```text
unstructured corroborating tourism text
```

Metadata minimum:

- source_type = wikipedia;
- canonical entity id bila dapat ditautkan;
- region bila dapat ditentukan secara auditable;
- revision/fetch timestamp;
- source family.

### D3 — Tourism News

Peran:

```text
time-sensitive unstructured tourism evidence
```

Metadata minimum:

- publisher;
- URL;
- published_at;
- fetched_at;
- source_type = news;
- linked tourism entity bila tersedia;
- region;
- story/origin lineage bila memungkinkan.

### D4 — Wikidata

Peran utama:

```text
entity mapping / canonical metadata support
```

Wikidata tidak harus menjadi vector corpus utama. Gunakan terutama untuk entity resolution dan metadata enrichment apabila field yang dibutuhkan tersedia.

---

## 10. Corpus Construction Rules

Setiap vector point wajib mempunyai:

```text
doc_id
chunk_id
text
embedding
source_type
source_id
entity_id (nullable jika tidak dapat ditautkan)
region metadata
category metadata
published_at / observed_at bila relevan
fetched_at
snapshot_id
```

Aturan:

1. snapshot sumber dibekukan sebelum benchmark utama;
2. embedding model dan versinya dibekukan;
3. dimension embedding tidak berubah antar metode;
4. satu shared graph digunakan oleh metode predicate-agnostic;
5. metadata-specific graph tidak dibangun untuk AdaptiveL;
6. document chunking dilakukan karena kebutuhan panjang dokumen, **bukan untuk menggelembungkan jumlah vector**;
7. duplicate dan syndicated text dicatat agar tidak mendominasi workload.

---

## 11. Minimum Corpus Gate

Sebelum eksperimen utama, laporkan:

```text
N documents
N vectors
N entities
N regions
N categories
N publishers
N temporal records
```

Gate praktis penelitian:

- jika corpus sangat kecil, fokuskan klaim pada correctness dan controlled behavior;
- jangan menyimpulkan scalability dari dataset kecil;
- match-rate regime hanya boleh digunakan jika setiap query-filter pair mempunyai set eligible yang cukup untuk top-k target;
- jangan membuat synthetic duplication hanya untuk memperbesar N.

---

## 12. Embedding Protocol

Pilih **satu** embedding model untuk main experiment.

Konfigurasi wajib dibekukan:

```text
model_name
model_version
embedding_dimension
normalization
similarity_metric
batch_size
precision / dtype
```

Similarity metric harus konsisten antara:

```text
exact filtered ground truth
DiskANN graph
all approximate-search methods
```

Embedding model bukan novelty.

Jika resource terbatas, embedding boleh dilakukan batch/offline dan vector hasilnya disimpan sebagai frozen artifact.

---

## 13. Metadata Predicate Model

Setiap query adalah pasangan:

```text
(q, f_q)
```

Dengan:

- `q` = semantic query vector;
- `f_q` = predicate atas metadata point.

Contoh single predicates:

```text
region = "Tanggamus"
category = "Desa Wisata"
source_type = "news"
published_at >= cutoff_time
publisher = X
```

Contoh compound predicates:

```text
region = "Tanggamus"
AND source_type = "news"
```

```text
category = "Desa Wisata"
AND published_at >= cutoff_time
```

```text
region = R
AND source_type IN {"news", "wikipedia"}
AND published_at >= cutoff_time
```

Compound predicate harus berasal dari metadata nyata corpus, bukan label sintesis yang hanya dibuat untuk eksperimen.

---

## 14. Filter Match Rate / Selectivity

Untuk predicate `f_q`, definisikan:

```text
match_rate(f_q) =
number of indexed points satisfying f_q
---------------------------------------
number of all indexed points
```

Interpretasi:

```text
lower match rate -> more selective filter
higher match rate -> broader filter
```

Paper acuan menunjukkan bahwa selective filters merupakan regime penting karena naive/post-filter approaches dapat gagal menemukan cukup banyak predicate-satisfying points.

DSIC-2906 akan membagi query-filter pairs ke beberapa empirical match-rate regime.

**Jangan menyalin threshold paper secara buta.**

Prosedur:

1. audit distribusi match rate pada corpus;
2. bentuk bins yang cukup terisi;
3. pastikan setiap bin mempunyai jumlah query yang memadai;
4. freeze bin boundaries sebelum final benchmark;
5. laporkan median dan range match rate aktual per bin.

Paper ranges boleh dipakai sebagai reference point, bukan kewajiban.

---

## 15. Query Workload

### Q1 — Region-Constrained Semantic Search

Contoh:

```text
query: "wisata bahari untuk melihat lumba-lumba"
filter: regency = "Tanggamus"
```

### Q2 — Category-Constrained Search

```text
query: "wisata alam dengan aktivitas konservasi"
filter: category = <natural category>
```

### Q3 — Source-Constrained Search

```text
query: <tourism information need>
filter: source_type = "news"
```

### Q4 — Time-Constrained Search

```text
query: <time-sensitive tourism information need>
filter: published_at within frozen time window
```

Q4 hanya menggunakan records yang benar-benar mempunyai temporal metadata yang valid.

### Q5 — Compound Filter Search

```text
query: <tourism information need>
filter:
    region = R
    AND source_type = S
    AND optional temporal predicate
```

Q1–Q3 wajib.

Q4 wajib jika temporal coverage memadai.

Q5 merupakan extension utama terhadap simple-filter workload.

---

## 16. Query Set Construction

Prioritas sumber query:

1. real Sigerciv search/query logs bila tersedia dan dapat digunakan secara etis;
2. query yang diturunkan dari kebutuhan informasi pengguna/domain experts;
3. held-out tourism text yang tidak identik dengan indexed item.

Jika query dibuat secara manual atau dengan template:

- template dibekukan;
- seed dibekukan;
- tidak diubah berdasarkan hasil metode;
- provenance setiap query disimpan.

Jangan memasukkan exact indexed text sebagai query tanpa exclusion rule, karena self-match dapat menggelembungkan recall secara artifisial.

---

## 17. Exact Filtered Ground Truth

Recall approximate search harus dihitung terhadap **exact filtered kNN**.

Untuk setiap `(q, f_q)`:

```text
P_f = {p in P | f_q(metadata(p)) = true}
```

Kemudian hitung exact top-k berdasarkan distance pada `P_f`:

```text
GT_k(q, f_q) = exact k nearest eligible points
```

Query-filter pair hanya valid untuk recall@k jika:

```text
|P_f| >= k
```

Ground truth dibuat **sekali** dari frozen vectors dan frozen metadata.

Jangan menggunakan hasil AdaptiveL sebagai ground truth.

---

## 18. Search Methods

### G0 — Exact Filtered Search

Peran:

```text
ground truth / oracle accuracy
```

Implementasi:

1. apply predicate;
2. brute-force distance terhadap seluruh eligible points;
3. return exact top-k.

Bukan competitor throughput utama bila corpus besar.

---

### B0 — Naive ANN + Post-Filtering

Prosedur:

1. jalankan unfiltered ANN;
2. ambil candidate list;
3. apply metadata predicate setelah retrieval;
4. return top-k predicate-satisfying points.

Tujuan:

```text
baseline paling sederhana
```

Kelemahan yang diuji:

```text
under-filled top-k pada low match-rate filters
```

Candidate budget wajib dicatat.

---

### B1 — TwoHopSearch

Implementasikan baseline mengikuti paper acuan.

Inti metode:

- graph traversal tetap mempertimbangkan distance;
- evaluate predicate pada neighbors;
- bila terlalu sedikit one-hop neighbors memenuhi predicate, scan two-hop neighborhood;
- predicate-satisfying candidates dimasukkan ke search frontier/result candidate set.

Implementasi harus diuji dengan unit tests terhadap pseudocode paper sebelum benchmark utama.

---

### P1 — AdaptiveL

AdaptiveL menjadi metode utama.

Prinsip:

1. gunakan standard graph search tanpa membangun metadata-specific index;
2. selama traversal, hitung jumlah visited nodes;
3. hitung berapa visited nodes yang memenuhi predicate;
4. setelah `n_sample` observations, estimasi filter specificity/match rate;
5. jika match rate rendah, perluas search frontier;
6. jika match rate tinggi, pertahankan budget dekat unfiltered search;
7. batasi expansion dengan `m_max`.

Estimasi:

```text
sp_hat = n_match / n_sample
```

Scaling mengikuti Algorithm 3 pada paper acuan:

```text
if sp_hat == 0:
    multiplier = m_max
elif sp_hat >= 0.5:
    multiplier = 1
elif sp_hat >= 0.1:
    multiplier = 2
else:
    l = -log10(sp_hat)
    multiplier = min(m_max, 2^l)
```

Integrasi multiplier ke frontier/search-list size harus mengikuti implementasi AdaptiveL yang telah diverifikasi terhadap pseudocode/source implementation paper sebelum eksperimen dibekukan.

---

## 19. Optional Adaptation — Resource-Capped AdaptiveL

Bagian ini **opsional** dan tidak boleh menggantikan evaluasi P1 AdaptiveL asli.

Tujuan:

> menguji apakah frontier expansion AdaptiveL dapat dijalankan secara aman ketika query mempunyai hard resource budget.

Tambahkan guard seperti:

```text
max_visited_nodes
max_distance_comparisons
query_timeout_ms
memory/resource cap
```

Nama sementara:

```text
RC-AdaptiveL
```

Ini harus disebut sebagai **engineering adaptation under a fixed resource budget**, bukan algoritma baru, kecuali novelty-nya kemudian dibuktikan terhadap literature.

Main paper tetap harus mempunyai hasil **unaltered AdaptiveL** sebagai anchor.

---

## 20. DiskANN Configuration

Paper acuan memakai DiskANN.

DSIC-2906 juga menggunakan DiskANN sebagai primary proximity graph agar adaptasi metodologis dekat dengan paper.

Konfigurasi yang wajib dicatat:

```text
R
L_build
L_search
metric
threads
index build time
index size
memory footprint
```

Paper public experiment menggunakan konfigurasi `R = 64` dan `L = 100` sebagai salah satu setup, sedangkan production WebIQ menggunakan parameter yang berbeda.

Aturan DSIC-2906:

- parameter paper dapat dipakai sebagai initial anchor;
- tuning hanya dilakukan pada development queries;
- final parameter dibekukan sebelum held-out benchmark;
- semua metode menggunakan graph snapshot yang sama sejauh algoritmanya memungkinkan;
- parameter yang tidak sama harus diberi alasan eksplisit.

---

## 21. AdaptiveL Parameter Study

Parameter utama:

```text
L_search
n_sample
m_max
```

Paper production experiment menggunakan `m_max = 8` dan mengestimasi approximate match rate setelah 1000 vectors.

Karena corpus DSIC-2906 jauh lebih kecil, `n_sample = 1000` **tidak boleh disalin tanpa audit**.

Gunakan development set untuk mengevaluasi beberapa nilai yang masuk akal terhadap ukuran index, lalu freeze satu primary setting.

Contoh grid awal:

```text
m_max   in {2, 4, 8}
n_sample in {64, 128, 256, 512}  # hanya nilai yang feasible
```

Grid di atas adalah rancangan eksperimen DSIC-2906, bukan parameter yang diklaim berasal dari paper.

---

## 22. Resource-Constrained Profiles

Resource constraint harus eksplisit dan reproducible.

Gunakan Docker/cgroup atau VM profiles untuk membatasi:

```text
CPU cores
RAM
threads
optional query timeout
```

Jangan mengarang profile setelah melihat hasil.

Freeze 2–3 profiles sebelum final benchmark, misalnya:

```text
RC-small
RC-medium
RC-reference
```

Nilai vCPU/RAM aktual ditetapkan setelah hardware tersedia dan dicatat di:

```text
configs/resource_profiles.yaml
```

Seluruh metode diuji pada profile yang sama.

---

## 23. Experimental Controls

Variabel yang harus identik antar metode:

- corpus snapshot;
- embedding vectors;
- similarity metric;
- metadata snapshot;
- query workload;
- filter predicates;
- exact ground truth;
- graph/index snapshot bila applicable;
- hardware/resource profile;
- thread count;
- warm-up procedure;
- repetition count;
- timeout policy.

Tidak boleh mengubah predicate atau query setelah melihat metode mana yang unggul.

---

## 24. Main Metrics

### 24.1 Filtered Recall@k

```text
Recall@k =
|Retrieved_k ∩ ExactFilteredGT_k|
---------------------------------
                k
```

Primary:

```text
Recall@10
```

Gunakan `k` lain hanya sebagai secondary analysis.

### 24.2 Queries per Second

```text
QPS = completed queries / elapsed wall-clock time
```

Laporkan batch size, threads, warm-up, dan measurement interval.

### 24.3 Latency

Laporkan minimal:

```text
p50
p95
```

Opsional:

```text
p99
```

### 24.4 Predicate Satisfaction Rate

Semua returned points harus memenuhi predicate.

```text
predicate_satisfaction_rate =
valid returned points / all returned points
```

Expected correctness:

```text
100%
```

### 24.5 Under-Filled Result Rate

```text
queries returning fewer than k results
--------------------------------------
valid query-filter pairs
```

Penting untuk low match-rate filters.

---

## 25. Search-Cost Metrics

Catat per query bila implementasi memungkinkan:

```text
visited nodes
distance comparisons
predicate evaluations
frontier/search-list size
AdaptiveL multiplier
candidate count
timeout flag
```

Kemudian laporkan:

```text
median
p95
distribution by match-rate regime
```

Tujuan: menjelaskan **mengapa** recall/QPS berubah, bukan hanya melaporkan angka akhir.

---

## 26. Stability Metric

Paper acuan mendefinisikan stability sebagai overlap result sets ketika query identik dijalankan kembali pada kondisi yang sama.

Adaptasi DSIC-2906:

Untuk dua hasil top-k:

```text
R1, R2
```

hitung:

```text
overlap@k = |R1 ∩ R2| / k
```

Lakukan repeated identical queries pada:

```text
same index
same vectors
same metadata
same predicate
same resource profile
```

Jika metode deterministic dalam setup lokal, stability dapat mendekati 1.0. Itu tetap merupakan hasil yang harus dilaporkan, bukan dimanipulasi agar terlihat berbeda.

---

## 27. Primary Analysis

### A1 — Recall–QPS Curves

Untuk setiap search method:

```text
B0 PostFilter
B1 TwoHop
P1 AdaptiveL
```

variasikan search budget / `L_search` secara terkontrol.

Plot:

```text
x-axis = Recall@10
y-axis = QPS
```

Pisahkan plot berdasarkan match-rate regime seperti pola evaluasi paper acuan.

### A2 — Recall–Latency

```text
x-axis = Recall@10
y-axis = p95 latency
```

### A3 — Match Rate Sensitivity

```text
x-axis = filter match rate
y-axis = recall / latency / visited nodes
```

### A4 — Stability

Bandingkan repeated-query overlap untuk setiap metode dan predicate regime.

### A5 — Resource Cap

Bandingkan method ranking pada RC-small, RC-medium, dan RC-reference.

---

## 28. Experiment Matrix

### E0 — Corpus & Metadata Audit

Output:

- frozen source snapshot;
- vector count;
- metadata completeness;
- filter cardinalities;
- empirical match-rate distribution;
- duplicate audit;
- temporal coverage audit.

Gate:

```text
sufficient valid query-filter pairs for at least 3 match-rate regimes
```

---

### E1 — Exact Ground Truth & Index Sanity

1. generate frozen embeddings;
2. build exact filtered evaluator;
3. build DiskANN graph;
4. verify unfiltered ANN recall;
5. verify every filtered method returns only eligible points;
6. validate no self-match leakage.

---

### E2 — Main Single-Predicate Benchmark

Run:

```text
B0 PostFilter
B1 TwoHop
P1 AdaptiveL
```

pada:

```text
region
category
source
optional time predicate
```

Stratify by match rate.

Primary outputs:

```text
Recall@10
QPS
p50/p95 latency
under-filled rate
visited nodes
predicate evaluations
```

---

### E3 — Compound-Predicate Benchmark

Gunakan real combinations seperti:

```text
region AND source_type
category AND source_type
region AND temporal window
region AND source_type AND temporal window
```

Hanya predicate yang mempunyai valid natural support dalam corpus yang digunakan.

Analisis apakah behavior berbeda dari single predicates dengan match rate serupa.

---

### E4 — Resource-Constrained Benchmark

Untuk setiap method, jalankan workload yang sama pada semua frozen resource profiles.

Ukur:

```text
Recall@10
QPS
p50/p95 latency
peak RSS / memory
CPU utilization
visited nodes
under-filled rate
```

---

### E5 — AdaptiveL Ablation

Evaluasi:

```text
n_sample
m_max
L_search
```

Gunakan development workload.

Tujuan:

- menunjukkan sensitivity;
- memilih final primary configuration;
- menjelaskan failure pada extreme selectivity.

---

### E6 — Stability & Failure Analysis

Repeated queries minimal beberapa kali per query pada fixed conditions.

Audit failure cases:

1. insufficient eligible points;
2. highly selective predicate;
3. post-filter under-fill;
4. TwoHop early termination;
5. AdaptiveL excessive expansion;
6. timeout;
7. duplicate/syndicated dominance;
8. metadata error;
9. query leakage/self-match;
10. poor unfiltered ANN neighborhood;
11. compound-predicate sparsity;
12. high predicate-evaluation cost.

---

## 29. Statistical Analysis

Gunakan paired design karena query-filter pair yang sama diuji pada setiap metode.

Primary reporting:

- mean/median Recall@10;
- median dan p95 latency;
- QPS;
- 95% bootstrap confidence interval pada query-filter pair;
- stratified results by match-rate regime.

Untuk latency:

- warm-up terlebih dahulu;
- randomized method order bila memungkinkan;
- repeated measurements;
- jangan mencampur index build time dengan query latency.

Untuk multiple resource profiles, tampilkan raw effect size dan confidence intervals sebelum mempertimbangkan significance testing tambahan.

---

## 30. Reproducibility Rules

Freeze sebelum held-out benchmark:

```text
corpus snapshot
metadata snapshot
query set
filter set
match-rate bins
embedding model
vector normalization
DiskANN build parameters
search parameters
resource profiles
thread count
warm-up
repetition count
random seed
timeout policy
```

Setiap result row minimal mempunyai:

```text
run_id
query_id
filter_id
match_rate
method
resource_profile
L_search
n_sample
m_max
recall_at_10
latency_ms
visited_nodes
predicate_evaluations
returned_count
timeout
```

---

## 31. Architecture Minimum

```text
JADESTA snapshot
Wikipedia / Tourism News
Wikidata metadata support
        │
        ▼
Corpus normalization
        │
        ├── text
        └── natural metadata
        │
        ▼
Frozen Embeddings
        │
        ├──────────────► Exact Filtered kNN Ground Truth
        │
        ▼
Single Shared DiskANN Graph
        │
        ▼
Query Vector + Metadata Predicate
        │
        ├── B0 PostFilter
        ├── B1 TwoHopSearch
        └── P1 AdaptiveL
        │
        ▼
Benchmark Logger
        │
        ├── Recall@10
        ├── QPS
        ├── p50/p95 latency
        ├── visited nodes
        ├── predicate evaluations
        ├── under-filled rate
        ├── memory / CPU
        └── stability
```

---

## 32. Peran Tools

### Python

Digunakan untuk:

- data preparation;
- metadata audit;
- embedding pipeline;
- exact filtered ground truth;
- query workload generation;
- experiment runner;
- statistics;
- figures.

### DiskANN

Primary graph/vector search engine.

Digunakan untuk:

- shared proximity graph;
- unfiltered ANN sanity;
- TwoHop/AdaptiveL implementation atau instrumented adaptation.

Jika Python binding tidak mengekspos traversal yang dibutuhkan, gunakan instrumented C++ implementation/fork yang terdokumentasi. Jangan diam-diam mengganti algoritma.

### Parquet

Format sederhana untuk:

- corpus metadata;
- embeddings metadata map;
- query workload;
- ground truth;
- raw results;
- processed benchmark tables.

### MinIO / Iceberg

Opsional sebagai reproducibility/data-management layer bila stack sudah tersedia.

Bukan syarat ilmiah AdaptiveL.

### Spark / Trino

Tidak wajib untuk core experiment.

Gunakan hanya bila benar-benar diperlukan untuk preprocessing skala besar atau audit corpus. Jangan memasukkan keduanya hanya agar penelitian terlihat sebagai “big data”.

---

## 33. Quality Gate — Data

- [ ] Source snapshot frozen.
- [ ] Corpus manifest tersedia.
- [ ] Metadata schema frozen.
- [ ] Embedding configuration frozen.
- [ ] Vector count dilaporkan.
- [ ] Duplicate policy jelas.
- [ ] Temporal metadata diaudit.
- [ ] Filter cardinality table tersedia.
- [ ] Match-rate distribution tersedia.
- [ ] Query provenance tersedia.
- [ ] Self-match leakage dicegah.

---

## 34. Quality Gate — Algorithm

- [ ] Exact filtered ground truth lolos unit test.
- [ ] B0 PostFilter lolos predicate correctness.
- [ ] B1 TwoHop sesuai pseudocode paper.
- [ ] P1 AdaptiveL sesuai prinsip Algorithm 2/3 paper.
- [ ] Semua method menggunakan similarity metric yang sama.
- [ ] Semua returned points memenuhi predicate.
- [ ] Instrumentation visited-node tersedia atau keterbatasannya dijelaskan.
- [ ] Search parameter freeze dilakukan sebelum held-out benchmark.

---

## 35. Quality Gate — Experiment

- [ ] Same queries across methods.
- [ ] Same predicates across methods.
- [ ] Same exact ground truth.
- [ ] Same index snapshot.
- [ ] Same resource profile.
- [ ] Same thread count.
- [ ] Same timeout policy.
- [ ] Warm-up dilakukan.
- [ ] Repetition count frozen.
- [ ] Recall@10 tersedia.
- [ ] QPS tersedia.
- [ ] p50/p95 latency tersedia.
- [ ] Under-filled rate tersedia.
- [ ] Match-rate stratification tersedia.
- [ ] Stability tersedia.
- [ ] Failure cases diaudit.

---

## 36. Quality Gate — Article

- [ ] Paper Liu et al. menjadi methodological anchor.
- [ ] Adapted components dinyatakan eksplisit.
- [ ] Perbedaan dari WebIQ dinyatakan eksplisit.
- [ ] Tidak mengklaim new algorithm tanpa bukti.
- [ ] Tidak mengklaim first tanpa literature verification.
- [ ] Related work mencakup Filtered-DiskANN, ACORN, NaviX, SIEVE, CAPS dari reference trail paper acuan.
- [ ] Main figure mempunyai recall–QPS curves per match-rate regime.
- [ ] Stability dilaporkan.
- [ ] Resource profile dilaporkan.
- [ ] Compound predicate evaluation dilaporkan.
- [ ] Artifact dapat mereproduksi minimal satu main table dan satu main figure.

---

## 37. Scientific Completion Criteria

Penelitian tetap selesai walaupun AdaptiveL **tidak** mengungguli TwoHopSearch pada tourism corpus.

Hasil yang sah antara lain:

```text
AdaptiveL unggul hanya pada low match-rate filters
AdaptiveL unggul pada recall tetapi lebih mahal di latency
TwoHop lebih baik pada corpus kecil
post-filter cukup baik ketika match rate tinggi
compound predicates menghilangkan keuntungan AdaptiveL
resource cap membatasi frontier expansion
stability tidak berbeda secara material
```

Jangan mengubah hipotesis atau workload untuk memaksa AdaptiveL menang.

---

## 38. Threats to Validity

### Corpus Scale

Tourism corpus jauh lebih kecil daripada WebIQ. Jangan menggeneralisasi hasil menjadi web-scale behavior.

### Domain Specificity

JADESTA/news tourism mempunyai distribusi metadata dan semantic density yang berbeda dari YFCC/Caselaw/WebIQ.

### Query Representativeness

Query buatan/manual mungkin tidak mencerminkan real production traffic.

### Filter Distribution

Beberapa natural filters mungkin terlalu broad atau terlalu selective.

### Exact Ground Truth Cost

Exact filtered kNN feasible hanya jika corpus/eligible set masih dapat dihitung secara offline.

### Embedding Bias

Hasil ANN dipengaruhi representasi embedding. Karena itu embedding model harus dibekukan dan bukan bagian dari tuning per method.

### Metadata Quality

Region/category/source/time yang salah akan mengubah eligible set dan ground truth.

### Duplicate Text

Duplicate atau syndicated content dapat menyebabkan neighborhood dan stability terlihat lebih baik daripada sebenarnya.

### Resource Emulation

Docker/cgroup tidak selalu identik dengan dedicated hardware.

### Implementation Fidelity

Kesalahan implementasi TwoHop atau AdaptiveL dapat disalahartikan sebagai behavior algoritma.

Karena itu pseudocode-to-code tests wajib.

---

## 39. Rencana Kerja 1 Bulan

### Minggu 1 — Corpus, Metadata, Embeddings, Ground Truth

Hari 1–2:

- freeze RQ dan publication boundary;
- baca ulang paper acuan dan implement Algorithm 2/3 notes;
- audit JADESTA;
- freeze metadata schema;
- tentukan embedding model;
- siapkan corpus manifest.

Hari 3–4:

- acquire/normalize optional Wikipedia/news;
- build text corpus;
- embedding batch;
- metadata completeness audit;
- duplicate audit.

Hari 5–7:

- build query workload;
- build natural filter workload;
- compute filter cardinalities;
- define match-rate regimes;
- exact filtered kNN ground truth;
- freeze development/test split.

### Minggu 2 — DiskANN, TwoHop, AdaptiveL

Hari 8–10:

- build DiskANN index;
- unfiltered ANN sanity;
- implement B0 PostFilter;
- predicate correctness tests.

Hari 11–12:

- implement TwoHopSearch;
- unit tests;
- instrumentation.

Hari 13–14:

- implement AdaptiveL;
- verify specificity estimator;
- verify frontier scaling;
- development benchmark;
- freeze primary parameters.

### Minggu 3 — Main Experiments

Hari 15–17:

- single-predicate benchmarks;
- recall–QPS curves;
- latency;
- under-filled rates.

Hari 18–19:

- compound-predicate benchmark;
- match-rate sensitivity.

Hari 20–21:

- resource profiles;
- stability runs;
- AdaptiveL ablation;
- results v1 freeze.

### Minggu 4 — Analysis, Reproduction, Article

Hari 22–24:

- bootstrap CI;
- failure analysis;
- main tables;
- main figures;
- clean rerun.

Hari 25–26:

- literature verification;
- related work trail;
- threats to validity;
- novelty wording audit.

Hari 27–28:

- Methods;
- Results;
- Discussion;
- limitations.

Hari 29–30:

- artifact freeze;
- reproduce one main table;
- reproduce one main figure;
- manuscript v0.8–v1.0;
- supervisor review.

---

## 40. Grafik dan Tabel Wajib

1. Corpus and metadata statistics table.
2. Filter cardinality and match-rate distribution table.
3. Architecture diagram.
4. Recall@10–QPS curve untuk setiap match-rate regime.
5. Recall@10–p95 latency plot.
6. Match rate vs recall plot.
7. Match rate vs visited nodes plot.
8. Under-filled result rate table.
9. Single vs compound predicate comparison.
10. Resource-profile comparison table.
11. Stability overlap table/plot.
12. AdaptiveL parameter-ablation table.
13. Failure taxonomy table.
14. Reproduction checklist.

Main paper minimal harus mempunyai item 1, 2, 4, 8, 9, 10, dan 11.

---

## 41. Struktur Repository

```text
dsic-2906/
├── README.md
├── .gitignore
├── .env.example
├── pyproject.toml
├── requirements.txt
├── Makefile
├── configs/
│   ├── corpus.yaml
│   ├── metadata.yaml
│   ├── embedding.yaml
│   ├── diskann.yaml
│   ├── search.yaml
│   ├── workload.yaml
│   ├── resource_profiles.yaml
│   └── experiment.yaml
├── data/
│   ├── README.md
│   ├── raw/
│   │   ├── jadesta/
│   │   ├── wikipedia/
│   │   ├── wikidata/
│   │   └── news/
│   ├── processed/
│   │   ├── corpus.parquet
│   │   ├── metadata.parquet
│   │   ├── queries.parquet
│   │   └── filters.parquet
│   ├── embeddings/
│   │   ├── base_vectors.*
│   │   └── query_vectors.*
│   ├── groundtruth/
│   │   └── filtered_knn_k10.parquet
│   └── manifests/
│       ├── source_manifest.csv
│       ├── corpus_manifest.csv
│       ├── vector_manifest.csv
│       └── workload_manifest.csv
├── index/
│   ├── README.md
│   └── diskann/
├── src/
│   ├── corpus/
│   │   ├── normalize.py
│   │   ├── metadata.py
│   │   ├── deduplicate.py
│   │   └── chunk.py
│   ├── embedding/
│   │   └── embed.py
│   ├── groundtruth/
│   │   └── exact_filtered_knn.py
│   ├── index/
│   │   ├── build_diskann.py
│   │   └── index_manifest.py
│   ├── search/
│   │   ├── postfilter.py
│   │   ├── twohop.py
│   │   ├── adaptivel.py
│   │   └── resource_capped_adaptivel.py   # optional
│   ├── workload/
│   │   ├── build_queries.py
│   │   ├── build_filters.py
│   │   └── stratify_match_rate.py
│   ├── benchmark/
│   │   ├── runner.py
│   │   ├── resource_monitor.py
│   │   ├── stability.py
│   │   └── logger.py
│   ├── evaluation/
│   │   ├── recall.py
│   │   ├── latency.py
│   │   ├── throughput.py
│   │   ├── bootstrap.py
│   │   ├── failure_analysis.py
│   │   └── plots.py
│   └── utils/
├── tests/
│   ├── test_predicates.py
│   ├── test_exact_groundtruth.py
│   ├── test_postfilter.py
│   ├── test_twohop.py
│   ├── test_adaptivel.py
│   └── test_workload_freeze.py
├── scripts/
│   ├── 00_audit_corpus.sh
│   ├── 01_build_corpus.sh
│   ├── 02_embed.sh
│   ├── 03_build_queries.sh
│   ├── 04_build_filters.sh
│   ├── 05_groundtruth.sh
│   ├── 06_build_index.sh
│   ├── 07_dev_benchmark.sh
│   ├── 08_freeze_params.sh
│   ├── 09_main_single_filters.sh
│   ├── 10_main_compound_filters.sh
│   ├── 11_resource_benchmark.sh
│   ├── 12_stability.sh
│   ├── 13_ablation.sh
│   └── 14_report.sh
├── results/
│   ├── raw/
│   ├── processed/
│   ├── figures/
│   ├── tables/
│   └── failure_cases/
├── docs/
│   ├── methodology-map.md
│   ├── paper-adaptation-notes.md
│   ├── workload-protocol.md
│   ├── reproducibility.md
│   └── failure-taxonomy.md
└── paper/
    ├── manuscript.md
    └── references.bib
```

---

## 42. Minimal Experiment Contract

Eksperimen belum boleh dijalankan sebagai final benchmark sebelum file berikut frozen:

```text
configs/embedding.yaml
configs/diskann.yaml
configs/search.yaml
configs/workload.yaml
configs/resource_profiles.yaml
data/manifests/corpus_manifest.csv
data/manifests/vector_manifest.csv
data/manifests/workload_manifest.csv
```

Tambahkan checksum untuk:

```text
base vectors
query vectors
metadata table
DiskANN index
exact ground truth
```

---

## 43. Expected Main Result Table

Format minimum:

| Match-rate regime | Predicate type | Method | Recall@10 | QPS | p50 ms | p95 ms | Under-filled % | Visited nodes | Predicate evals | Stability |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| low | region | PostFilter | | | | | | | | |
| low | region | TwoHop | | | | | | | | |
| low | region | AdaptiveL | | | | | | | | |
| medium | compound | PostFilter | | | | | | | | |
| medium | compound | TwoHop | | | | | | | | |
| medium | compound | AdaptiveL | | | | | | | | |

Jangan mengisi angka dummy pada manuscript final.

---

## 44. Expected Main Claims

Claim hanya boleh dibuat jika evidence eksperimen mendukung.

Contoh claim yang valid **jika hasil mendukung**:

```text
AdaptiveL preserved higher filtered recall than TwoHopSearch
in the lowest empirical match-rate regime at comparable throughput.
```

```text
The advantage diminished as filter match rate increased.
```

```text
Compound predicates increased search effort even when their final
match rate was similar to selected single-predicate workloads.
```

```text
Under tighter resource caps, AdaptiveL's frontier expansion improved
recall but increased tail latency.
```

Jika hasil berbeda, claim harus mengikuti hasil aktual.

---

## 45. Reference Trail dari Paper Acuan

Minimum papers yang perlu dibaca sebelum final Related Work:

1. Liu et al. — **Metadata-Filtered Vector Search in the WebIQ Grounding Index**.
2. Gollapudi et al. — **Filtered-DiskANN: Graph Algorithms for Approximate Nearest Neighbor Search with Filters**.
3. Patel et al. — **ACORN: Performant and Predicate-Agnostic Search Over Vector Embeddings and Structured Data**.
4. Sehgal & Salihoglu — **NaviX: A Native Vector Index Design for Graph DBMSs With Robust Predicate-Agnostic Search Performance**.
5. Li et al. — **SIEVE: Effective Filtered Vector Search with Collection of Indexes**.
6. Gupta et al. — **CAPS: A Practical Partition Index for Filtered Similarity Search**.
7. Cai et al. — **Navigating Labels and Vectors: A Unified Approach to Filtered Approximate Nearest Neighbor Search**.
8. Simhadri et al. — DiskANN repository/paper trail.

Daftar ini berasal dari reference trail paper acuan dan harus diverifikasi ulang ketika menulis bibliography final.

---

## 46. Primary Reference

Liu, F., Manohar, M., Chen, Q., Tan, L., Zhang, J., He, X., Deyneko, D., Truong, S., Phull, A., Kaminaga, G., Sharma, V., Liu, Z., Li, Z., & Risvik, K. (2026). **Metadata-Filtered Vector Search in the WebIQ Grounding Index**. *VLDB 2026 Workshop: The 2nd Workshop on Vector Databases*.

---

## 47. Definisi Selesai

DSIC-2906 dinyatakan selesai ketika:

```text
[ ] corpus dan metadata snapshot frozen
[ ] embeddings frozen
[ ] exact filtered kNN ground truth tersedia
[ ] DiskANN shared index tersedia
[ ] PostFilter baseline tersedia
[ ] TwoHopSearch tersedia dan teruji
[ ] AdaptiveL tersedia dan teruji
[ ] single-predicate workload selesai
[ ] compound-predicate workload selesai
[ ] minimal 3 empirical match-rate regimes dianalisis
[ ] Recall@10–QPS curves tersedia
[ ] p50/p95 latency tersedia
[ ] under-filled result rate tersedia
[ ] stability tersedia
[ ] resource-constrained benchmark tersedia
[ ] failure analysis tersedia
[ ] satu main table dapat direproduksi
[ ] satu main figure dapat direproduksi
[ ] paper tidak overclaim novelty
```

---

## Ringkasan Satu Kalimat

> **Penelitian ini adalah controlled adaptation dan evaluation of AdaptiveL untuk metadata-filtered vector search pada heterogeneous tourism evidence, dengan fokus pada filter selectivity, compound predicates, recall–throughput trade-offs, stability, dan resource-constrained behavior.**
