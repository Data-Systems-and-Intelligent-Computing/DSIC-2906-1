# Data layout

This repository tracks manifests and schemas, not raw/source payloads or generated vectors.

- `raw/`: frozen source snapshots (ignored by Git).
- `processed/`: generated `corpus.parquet`, `metadata.parquet`, `queries.parquet`, `filters.parquet`.
- `embeddings/`: frozen base/query vectors.
- `groundtruth/`: exact filtered kNN results.
- `manifests/`: provenance and checksum tables used to freeze the experiment.

Do not create synthetic duplicate records merely to increase corpus size.
