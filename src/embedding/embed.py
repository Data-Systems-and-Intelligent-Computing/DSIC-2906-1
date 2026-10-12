"""Embedding korpus DSIC-2906-1 dengan satu model beku (Protokol bagian 19; README bagian 12).

Jalankan dari root repo:  python -m src.embedding.embed

Output:
    data/embeddings/base_vectors.npy     matriks float32 (n_dokumen x dimensi)
    data/embeddings/base_ids.parquet     urutan doc_id yang sama dengan baris matriks
    data/manifests/vector_manifest.csv   model, versi, dimensi, checksum
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
from sentence_transformers import SentenceTransformer

from src.utils.hashing import sha256


# Konfigurasi embedding yang sudah dibekukan
def load_embedding_config(path: str = "configs/embedding.yaml") -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


# Perangkat komputasi: GPU Apple (mps) bila ada, selain itu CPU
def pick_device() -> str:
    return "mps" if torch.backends.mps.is_available() else "cpu"


def main() -> None:
    cfg = load_embedding_config()
    if not cfg.get("model_version") or not cfg.get("embedding_dimension"):
        raise SystemExit("model_version dan embedding_dimension di configs/embedding.yaml wajib diisi (dibekukan).")

    # Teks dokumen dan doc_id dari korpus beku
    corpus = pd.read_parquet("data/processed/corpus.parquet", columns=["doc_id", "text", "snapshot_id"])
    texts = corpus["text"].tolist()

    # Model pada versi persis yang tercatat di config
    device = pick_device()
    torch.manual_seed(cfg["random_seed"])
    model = SentenceTransformer(cfg["model_name"], revision=cfg["model_version"], device=device)
      dim = model.get_embedding_dimension()
    if dim != cfg["embedding_dimension"]:
        raise SystemExit(f"Dimensi model {dim} tidak sama dengan config {cfg['embedding_dimension']}.")

    # Proses embedding seluruh dokumen
    t0 = time.time()
    vectors = model.encode(
        texts,
        batch_size=cfg["batch_size"],
        normalize_embeddings=cfg["normalize_embeddings"],
        convert_to_numpy=True,
        show_progress_bar=True,
    ).astype(cfg["dtype"])
    elapsed = time.time() - t0

    # Penyimpanan vektor dan urutan doc_id (baris ke-i matriks = doc_id ke-i)
    os.makedirs("data/embeddings", exist_ok=True)
    np.save("data/embeddings/base_vectors.npy", vectors)
    corpus[["doc_id"]].to_parquet("data/embeddings/base_ids.parquet", index=False)

    # Manifest vektor untuk pembekuan (README bagian 42)
    pd.DataFrame([{
        "artifact": "data/embeddings/base_vectors.npy",
        "model_name": cfg["model_name"],
        "model_version": cfg["model_version"],
        "dimension": dim,
        "dtype": cfg["dtype"],
        "normalized": cfg["normalize_embeddings"],
        "metric": cfg["similarity_metric"],
        "n_vectors": len(vectors),
        "checksum_sha256": sha256("data/embeddings/base_vectors.npy"),
    }]).to_csv("data/manifests/vector_manifest.csv", index=False)

    print(f"Selesai: {vectors.shape} | perangkat {device} | {elapsed:.1f} detik")
    print(f"snapshot korpus: {corpus['snapshot_id'].iloc[0]}")


if __name__ == "__main__":
    main()