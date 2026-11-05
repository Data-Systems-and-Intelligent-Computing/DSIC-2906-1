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
## 3. Method

### 3.1 Corpus
The corpus contains 64,354 documents: 15,132 tourism attractions and 6,329 tourism villages from JADESTA, and 42,893 online news articles. The news articles are the unique URLs among 71,579 attraction–news pairs collected for the attractions. This corpus is small to medium in size compared with the web-scale WebIQ index of the reference paper.

Each document becomes exactly one vector; no chunking is applied. Attraction text concatenates the attraction name, its category, its address, and its listed facilities. Village text concatenates the village name, its village type, its address, and its facilities. News text is the article title, with the source suffix appended by Google News removed. As a result, JADESTA texts are longer than news texts (median 133–152 versus 74 characters) and follow a fixed template; this asymmetry is discussed in Section 6.1.

### 3.2 Natural metadata
Every document carries the metadata that occurs naturally in its source. Regency (kabupaten/kota) has 483 distinct values. News articles inherit the regencies of all attractions they are linked to; 9,804 articles are linked to more than one regency, and a predicate on such an article is satisfied when any of its values matches (any-match rule). Category has four values (alam, budaya, buatan, desa), tourism villages additionally carry a maturity level, and source type has three values (attraction, village, news).

The raw province column is not used. Province is derived from the regency through the official regional code table of the Ministry of Home Affairs (Kepmendagri 300.2.2-2138/2025, as amended by 300.2.2-2430/2025), extended with 18 manually reviewed spelling aliases. Documents whose regency field is empty or does not contain a regency name (174 documents) receive no province.

Publisher domains of news articles are normalized by merging subdomains of the same publisher, which reduces 3,862 domains to 2,808 publishers. Syndicated news, i.e., near-identical titles published within two days, is grouped with a fuzzy-match threshold of 90 into 768 story lineages covering 1,606 articles; a manual review of all 342 groups with non-identical titles found 10 false positives (2.9%).

### 3.3 Embedding and shared index
All documents and queries are embedded with the frozen model paraphrase-multilingual-MiniLM-L12-v2 (384 dimensions) and compared by cosine distance on normalized vectors. A single Vamana proximity graph is built once with DiskANN (diskannpy 0.7.0; R = 64, L_build = 100, alpha left at the library default) and shared by all methods, so that differences between methods are not caused by different indexes. Unfiltered search on this graph reaches a recall@10 of 0.9959. Because the DiskANN Python bindings do not expose graph traversal, the greedy search and all three filtered methods are reimplemented in Python on top of the same graph file.

### 3.4 Search methods
PostFilter runs unfiltered greedy search with a frontier of size equal to its candidate budget and then applies the predicate to the returned candidates; when fewer than k candidates pass, the result is under-filled. TwoHopSearch follows Algorithm 1 of the reference paper: only points that satisfy the predicate enter the frontier, and when more than half of a visited point's neighbors fail the predicate, the neighbors of those failing points are also evaluated. AdaptiveL follows Algorithms 2 and 3: after n_sample visits it estimates the predicate specificity ŝp from the fraction of visited points that match, and rescales the frontier size once by a multiplier of at most m_max.

The frozen parameters are a candidate budget of [TBD] for PostFilter, L ∈ [TBD] for TwoHopSearch, and L ∈ [TBD] with n_sample = [TBD] and m_max = [TBD] for AdaptiveL. All methods share a per-query timeout of [TBD] ms, derived from the development benchmark as three times the maximum observed latency. Parameters were chosen on a separate development set of 100 queries and frozen before the test workload was run.

### 3.5 Workload and exact ground truth
Predicates are drawn from the metadata that actually occurs in the corpus. Single predicates cover regency, province, publisher, category, source type, and publication date; compound predicates are regency ∧ category, regency ∧ news published in 2026, province ∧ source type, and category ∧ publication date. Each predicate is assigned to a match-rate bin with boundaries at 0.1%, 0.5%, 2.5%, and 10% (B1–B5). A predicate enters the main set when at least 10k points satisfy it and the extension set when at least k but fewer than 10k do; the two sets are reported separately.

For each cell of set, bin, and predicate type, up to 10 predicates and about 60 query–filter pairs are sampled with a fixed seed (2906), half of them with the query document inside the filter. Queries are corpus documents with at least four words, excluding the development queries. Query documents remain in the index; for each query, its own document, documents with an identical vector, and documents in the same story lineage are removed from that query's eligible set only. The frozen workload contains 2,040 query–filter pairs over 2,008 distinct queries. Ground truth is the exact filtered k-nearest-neighbor set (k = 10) under cosine distance, with ties broken by row index.

### 3.6 Metrics
Accuracy is measured as filtered recall@10 against the exact ground truth, with 95% confidence intervals from a 2,000-iteration bootstrap over query–filter pairs. Throughput is reported as queries per second and latency as p50 and p95. Search cost is measured by visited nodes, distance comparisons, and predicate evaluations (total and unique). We also report the under-filled rate (results with fewer than k items) and stability as the overlap@10 between repeated runs of identical queries. All benchmarks run on an AWS Lightsail t3.xlarge instance (burstable CPU, shared host) with a single thread. Because traversal is implemented in Python, QPS and latency are secondary results; the main cost comparisons use distance comparisons and predicate evaluations.

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
### 6.1 Threats to Validity

**Corpus scale.** The corpus contains 64,354 documents, which is small to medium in size compared with the web-scale WebIQ index of the reference paper. We therefore make no claims about scalability and restrict our conclusions to correctness and controlled search behavior.

**Domain specificity.** Tourism evidence from JADESTA and online news has metadata distributions and semantic density that differ from the YFCC, Caselaw, and WebIQ collections used by Liu et al. (2026). Results may not transfer directly to other domains.

The corpus also contains only three source types (JADESTA attractions, JADESTA villages, and news); Wikipedia and Wikidata were not acquired, so source-type predicates have limited variety and encyclopedic text is not represented.

**Query representativeness.** Queries are 2,008 corpus documents with at least four words, not real user search logs. Query documents remain in the index; to prevent self-matches, each query's own document, documents with identical vectors, and documents in the same syndication lineage are removed from that query's eligible set only.

**Filter distribution.** Match-rate bins are confounded with predicate type: B5 contains only broad predicates, while B1 contains no single province or category predicates (province appears in B1 only in compound province ∧ source-type predicates). Comparisons between single and compound predicates are therefore restricted to B2–B3, where both types are present.

**Exact ground truth cost.** Exact filtered kNN ground truth is feasible only because the corpus is small; it was computed offline for all 2,040 query–filter pairs.

**Embedding bias and text asymmetry.** The embedding model (paraphrase-multilingual-MiniLM-L12-v2, 384 dimensions) is frozen and shared by all methods. However, news texts are about half as long as JADESTA texts (median 74 versus 133–152 characters), and JADESTA texts are generated from a structured template, which raises their similarity to nearest neighbors (median cosine 0.92–0.93 versus 0.82 for news). Differences in recall across source types therefore mix filter selectivity with representation effects and are interpreted with caution.

**Metadata quality.** The raw province column is not used. Province is derived from the regency name through the official Ministry of Home Affairs code table (Kepmendagri 300.2.2-2138/2025, as amended by 300.2.2-2430/2025), with 18 manually reviewed spelling aliases; documents whose regency field is empty or not a regency name (174 documents) receive no province. An earlier correction of the raw province column, made with the help of an AI coding tool (Antigravity) and used for workload v1, was replaced because its mapping table was not recorded; the workload and ground truth were re-frozen as v2 with the same seed, configuration, and bin boundaries. About 23% of news articles are linked to more than one regency and are matched with an any-match rule. (Robustness run on the frozen workload pending.)

**Duplicate text.** Syndicated news was grouped into 768 story lineages and excluded from each query's eligible set, so that duplicates do not inflate neighborhood quality or stability. All 342 lineage groups with non-identical titles (726 articles) were manually reviewed by the author: 10 groups (2.9%) were false positives, typically titles that differ only in a place name, number, or person's name. The threshold was kept fixed because the workload had already been frozen.

**Resource emulation.** (To be completed after the benchmark on an AWS Lightsail instance: t3.xlarge, burstable CPU, shared host.)

**Implementation fidelity.** TwoHopSearch and AdaptiveL were checked line by line against Algorithms 1–3 of the reference paper and are covered by unit tests (32 tests passing at commit 125c981; log in results/summary/pytest_2026-10-29.txt). Graph traversal is implemented in Python, so QPS and latency are reported as secondary results labeled "Python implementation", and the main cost curves use distance comparisons and predicate evaluations.

## 7. Conclusion
