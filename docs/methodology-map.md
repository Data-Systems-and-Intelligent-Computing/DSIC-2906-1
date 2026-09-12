# Methodology map

Primary methodological anchor: Liu et al. (2026), *Metadata-Filtered Vector Search in the WebIQ Grounding Index*.

| Anchor element | DSIC-2906 adaptation |
|---|---|
| Single shared graph | One frozen DiskANN graph over tourism evidence |
| Metadata predicate | Natural region/category/source/time/compound predicates |
| Match-rate regimes | Empirical bins from the frozen tourism corpus |
| TwoHopSearch | Baseline B1 |
| AdaptiveL | Primary method P1 |
| Recall vs QPS | Primary trade-off analysis |
| Result stability | Repeated-query top-k overlap |
| Web-scale production | Resource-constrained controlled environment |

The project is an adaptation/external evaluation unless later literature verification supports a stronger claim.
