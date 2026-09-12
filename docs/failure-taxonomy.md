# Failure taxonomy

Minimum categories:
- under-filled top-k after filtering;
- low filtered recall;
- timeout/resource cap;
- predicate evaluation mismatch;
- missing/incorrect metadata;
- duplicate or syndicated-content dominance;
- query self-match leakage;
- implementation deviation from paper pseudocode;
- unstable repeated-query results.

Audit concrete cases; do not infer cause solely from aggregate metrics.
