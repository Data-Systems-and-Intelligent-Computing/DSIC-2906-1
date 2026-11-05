"""Ground truth eksak G0 untuk seluruh pasangan kueri-filter (Protokol bagian 19 butir 1; README bagian 17).

Untuk setiap pasangan: eligible = titik yang memenuhi predikat dikurangi baris eksklusi self-match
pasangan itu, lalu k titik terdekat dihitung secara menyeluruh (tanpa aproksimasi) dengan pemecah
seri nomor baris. Ground truth dibuat sekali dari vektor dan metadata yang beku.

Jalankan dari root repo:  python -m src.groundtruth.build_groundtruth
Output:
    data/groundtruth/filtered_knn_k10.parquet
    data/manifests/groundtruth_manifest.csv
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from src.groundtruth.exact_filtered_knn import exact_filtered_knn
from src.utils.hashing import sha256
from src.workload.build_filters import filter_mask


# Mask eligible satu pasangan: predikat dikurangi baris eksklusi self-match
def eligible_for_pair(mask: np.ndarray, excluded: list[int]) -> np.ndarray:
    eligible = mask.copy()
    eligible[np.asarray(excluded, dtype=np.int64)] = False
    return eligible


def main(k: int = 10) -> None:
    corpus = pd.read_parquet("data/processed/corpus.parquet")
    vectors = np.load("data/embeddings/base_vectors.npy")
    workload = pd.read_parquet("data/processed/workload.parquet")

    masks: dict[str, np.ndarray] = {}
    rows = []
    for pr in workload.itertuples(index=False):
        if pr.filter_id not in masks:
            masks[pr.filter_id] = filter_mask(corpus, json.loads(pr.filter_id))
        eligible = eligible_for_pair(masks[pr.filter_id], pr.excluded_rows)
        if int(eligible.sum()) != pr.n_eligible:
            raise AssertionError(f"Jumlah eligible {pr.pair_id} tidak sama dengan workload")

        q = vectors[pr.query_row]
        gt = exact_filtered_knn(vectors, q, eligible, k=k)
        rows.append({
            "pair_id": pr.pair_id,
            "gt_rows": gt.tolist(),
            "gt_doc_ids": corpus["doc_id"].to_numpy()[gt].tolist(),
            "gt_dist": (1.0 - vectors[gt] @ q).astype(float).tolist(),
        })

    os.makedirs("data/groundtruth", exist_ok=True)
    out = "data/groundtruth/filtered_knn_k10.parquet"
    pd.DataFrame(rows).to_parquet(out, index=False)
    pd.DataFrame([{
        "artifact": out, "n_pairs": len(rows), "k": k, "metric": "cosine",
        "tie_break": "row_index_ascending",
        "workload_checksum_sha256": sha256("data/processed/workload.parquet"),
        "vectors_checksum_sha256": sha256("data/embeddings/base_vectors.npy"),
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "checksum_sha256": sha256(out),
    }]).to_csv("data/manifests/groundtruth_manifest.csv", index=False)
    print(f"Ground truth: {len(rows):,} pasangan -> {out}")


if __name__ == "__main__":
    main()
