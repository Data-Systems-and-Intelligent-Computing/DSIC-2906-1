# Workload protocol

1. Freeze source snapshots and metadata schema.
2. Build query-filter pairs from real/domain-expert/held-out sources.
3. Prevent exact self-match leakage.
4. Compute natural predicate cardinalities and empirical match rates.
5. Exclude Recall@k pairs with fewer than k eligible points.
6. Freeze match-rate bins before final benchmark.
7. Run identical query-filter pairs across all compared methods.
8. Report single and compound predicates separately.
