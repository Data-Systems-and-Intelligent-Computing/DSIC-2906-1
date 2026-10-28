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
  The corpus contains 64,354 documents (15,132 attractions, 6,329 tourism villages, and 42,893 news articles), which is small to medium in size compared with the web-scale WebIQ index of the reference paper.
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
### 6.1 Threats to Validity

**Corpus scale.** The corpus contains 64,354 documents, which is small to medium in size compared with the web-scale WebIQ index of the reference paper. We therefore make no claims about scalability and restrict our conclusions to correctness and controlled search behavior.

**Domain specificity.** Tourism evidence from JADESTA and online news has metadata distributions and semantic density that differ from the YFCC, Caselaw, and WebIQ collections used by Liu et al. (2026). Results may not transfer directly to other domains.

**Query representativeness.** Queries are 1,987 held-out corpus documents with at least four words, not real user search logs. Self-matches are prevented by excluding the query document, identical vectors, and documents in the same syndication lineage from each eligible set.

**Filter distribution.** Match-rate bins are confounded with predicate type: B5 contains only broad predicates, while B1 contains no province or category predicates. Comparisons between single and compound predicates are therefore restricted to B2–B3, where both types are present.

**Exact ground truth cost.** Exact filtered kNN ground truth is feasible only because the corpus is small; it was computed offline for all 2,034 query–filter pairs.

**Embedding bias and text asymmetry.** The embedding model (paraphrase-multilingual-MiniLM-L12-v2, 384 dimensions) is frozen and shared by all methods. However, news texts are about half as long as JADESTA texts (median 74 versus 133–152 characters), and JADESTA texts are generated from a structured template, which raises their similarity to nearest neighbors (median cosine 0.92–0.93 versus 0.82 for news). Differences in recall across source types therefore mix filter selectivity with representation effects and are interpreted with caution.

**Metadata quality.** Province values were corrected before corpus construction, and all 16,340 corrections are recorded in the normalization report. About 23% of news articles are linked to more than one regency and are matched with an any-match rule. A robustness run that excludes these ambiguous articles leaves B4–B5 results stable, but shifts two B2 predicates into the B1 regime, where the method ranking changes.

**Duplicate text.** Syndicated news was grouped into 768 story lineages and excluded from each query's eligible set, so that duplicates do not inflate neighborhood quality or stability. All 342 lineage groups with non-identical titles (726 articles) were manually reviewed by the author: 10 groups (2.9%) were false positives, typically titles that differ only in a place name, number, or person's name. The threshold was kept fixed because the workload had already been frozen.

**Resource emulation.** (To be completed after the benchmark on the GCP VM.)

**Implementation fidelity.** TwoHopSearch and AdaptiveL were checked line by line against Algorithms 1–3 of the reference paper and are covered by unit tests. Graph traversal is implemented in Python, so QPS and latency are reported as secondary results labeled "Python implementation", and the main cost curves use distance comparisons and predicate evaluations.

## 7. Conclusion
