"""Build and freeze query records with provenance (Protokol bagian 18; README bagian 15-16).

Langkah:
1. Populasi predikat alami: seluruh predikat tunggal dan majemuk dari metadata korpus,
   beserta jumlah titik eligible, match rate, dan bin.
2. Kelayakan: set utama (>= 10 x k titik) dan set ekstensi (>= k tetapi < 10 x k).
3. Sampling per sel (set, bin, tipe predikat): hingga `predicates_per_cell` predikat,
   total sekitar `pairs_per_cell` pasangan kueri-filter; separuh kuerinya memenuhi predikat.
4. Kueri = dokumen korpus yang ditahan (bukan kueri development), dengan eksklusi self-match:
   dokumen kueri, dokumen bervektor identik, dan dokumen satu story_lineage.

Jalankan dari root repo:  python -m src.workload.build_queries
Output:
    data/processed/filters.parquet    populasi predikat (untuk audit)
    data/processed/queries.parquet    kueri beserta provenance
    data/processed/workload.parquet   pasangan kueri-filter beku
    data/embeddings/query_vectors.npy vektor kueri (urutan = queries.parquet)
    data/manifests/workload_manifest.csv
"""
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.utils.hashing import sha256
from src.workload.build_filters import filter_mask, spec_id
from src.workload.stratify_match_rate import assign_bin

QUERY_COLUMNS = ["query_id", "query_text", "provenance", "created_by", "self_match_exclusion"]


# Jumlah titik untuk setiap kandidat predikat, dihitung sekaligus per tipe
def predicate_population(corpus: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    rows = []

    def tambah(tipe, jumlah: pd.Series, buat_spec):
        for nilai, n in jumlah.items():
            rows.append({"type": tipe, "spec": buat_spec(nilai), "n_eligible": int(n)})

    kab = corpus.explode("kabupaten")
    prov = corpus.explode("province")
    kat = corpus.explode("category")
    tgl = corpus["published_at"]
    is_news = corpus["source_type"] == "news"

    # Predikat tunggal
    tambah("kabupaten", kab["kabupaten"].value_counts(), lambda v: {"kabupaten": v})
    tambah("provinsi", prov["province"].value_counts(), lambda v: {"province": v})
    tambah("penerbit", corpus["publisher_id"].dropna().value_counts(), lambda v: {"publisher_id": v})
    tambah("kategori", kat["category"].value_counts(), lambda v: {"category": v})
    tambah("tipe_sumber", corpus["source_type"].value_counts(), lambda v: {"source_type": v})
    tambah("temporal", pd.Series({d: int((tgl >= pd.Timestamp(d)).sum()) for d in cfg["temporal_thresholds"]}),
           lambda d: {"published_at_gte": d})

    # Predikat majemuk dari kombinasi metadata yang benar-benar ada (README bagian 13)
    kk = corpus.explode("kabupaten").explode("category").groupby(["kabupaten", "category"])["doc_id"].nunique()
    tambah("kabupaten_kategori", kk, lambda v: {"kabupaten": v[0], "category": v[1]})
    b26 = corpus[is_news & (tgl >= pd.Timestamp("2026-01-01"))].explode("kabupaten")["kabupaten"].value_counts()
    tambah("kabupaten_news_2026", b26,
           lambda v: {"kabupaten": v, "source_type": "news", "published_at_gte": "2026-01-01"})
    ps = prov.groupby(["province", "source_type"])["doc_id"].nunique()
    tambah("provinsi_tipe_sumber", ps, lambda v: {"province": v[0], "source_type": v[1]})
    kt = pd.Series({(c, d): int(((tgl >= pd.Timestamp(d)) & corpus["category"].apply(lambda x: c in x)).sum())
                    for c in kat["category"].dropna().unique() for d in cfg["temporal_thresholds"]})
    tambah("kategori_temporal", kt[kt > 0], lambda v: {"category": v[0], "published_at_gte": v[1]})

    pop = pd.DataFrame(rows)
    pop["filter_id"] = pop["spec"].map(spec_id)
    pop["match_rate"] = pop["n_eligible"] / len(corpus)
    b = cfg["match_rate_binning"]
    pop["bin"] = assign_bin(pop["match_rate"] * 100, b["boundaries_pct"], b["labels"])
    k = cfg["k"]
    s = cfg["sufficiency"]
    pop["layak_utama"] = pop["n_eligible"] >= s["main_min_eligible_factor"] * k
    pop["layak_ekstensi"] = (pop["n_eligible"] >= s["extension_min_eligible_factor"] * k) & ~pop["layak_utama"]
    return pop.drop_duplicates("filter_id").reset_index(drop=True)


# Grup duplikat (vektor identik) dan story_lineage untuk eksklusi self-match
def exclusion_groups(corpus: pd.DataFrame, vectors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    _, dup_group = np.unique(vectors, axis=0, return_inverse=True)
    lineage = corpus["story_lineage_id"].fillna("").to_numpy()
    return dup_group.ravel(), lineage


def excluded_rows(qi: int, dup_group: np.ndarray, lineage: np.ndarray) -> np.ndarray:
    """Baris yang dikeluarkan dari himpunan eligible untuk kueri qi."""
    ex = (dup_group == dup_group[qi])
    if lineage[qi]:
        ex |= (lineage == lineage[qi])
    ex[qi] = True
    return np.flatnonzero(ex)


def main() -> None:
    cfg = yaml.safe_load(Path("configs/workload.yaml").read_text(encoding="utf-8"))
    k = cfg["k"]
    rng = np.random.default_rng(cfg["random_seed"])

    corpus = pd.read_parquet("data/processed/corpus.parquet")
    vectors = np.load("data/embeddings/base_vectors.npy")
    N = len(corpus)

    # Populasi predikat dan kelayakannya
    pop = predicate_population(corpus, cfg)
    os.makedirs("data/processed", exist_ok=True)
    pop.assign(spec=pop["spec"].map(spec_id)).to_parquet("data/processed/filters.parquet", index=False)

    # Kumpulan kandidat kueri: cukup panjang dan bukan kueri development
    dev = cfg["dev_queries"]
    dev_rows = set(np.random.default_rng(dev["seed"]).choice(N, size=dev["n"], replace=False).tolist())
    n_words = corpus["text"].str.split().str.len().to_numpy()
    pool = np.array([i for i in range(N) if n_words[i] >= cfg["min_query_words"] and i not in dev_rows])
    in_pool = np.zeros(N, dtype=bool)
    in_pool[pool] = True
    dup_group, lineage = exclusion_groups(corpus, vectors)

    # Sel (set, bin, tipe): set utama untuk predikat layak_utama, set ekstensi untuk layak_ekstensi
    sm = cfg["sampling"]
    pairs = []
    for set_name, col in (("utama", "layak_utama"), ("ekstensi", "layak_ekstensi")):
        need = (cfg["sufficiency"]["main_min_eligible_factor"] if set_name == "utama"
                else cfg["sufficiency"]["extension_min_eligible_factor"]) * k
        for (b, tipe), cell in pop[pop[col]].groupby(["bin", "type"]):
            pilih = cell.sample(n=min(sm["predicates_per_cell"], len(cell)), random_state=int(rng.integers(1 << 31)))
            per_pred = math.ceil(sm["pairs_per_cell"] / len(pilih))
            for _, pr in pilih.iterrows():
                mask = filter_mask(corpus, pr["spec"])
                n_in = int(round(per_pred * sm["query_in_filter_fraction"]))
                for in_filter, n_q in ((True, n_in), (False, per_pred - n_in)):
                    kandidat = np.flatnonzero(in_pool & (mask if in_filter else ~mask))
                    rng.shuffle(kandidat)
                    dipakai = 0
                    for qi in kandidat:
                        if dipakai == n_q:
                            break
                        ex = excluded_rows(int(qi), dup_group, lineage)
                        n_eligible = int(mask.sum() - mask[ex].sum())
                        if n_eligible < need:
                            continue
                        pairs.append({
                            "set": set_name, "bin": b, "type": tipe, "filter_id": pr["filter_id"],
                            "n_eligible_raw": int(pr["n_eligible"]), "n_eligible": n_eligible,
                            "match_rate": float(pr["match_rate"]), "query_row": int(qi),
                            "query_doc_id": corpus["doc_id"].iat[qi], "query_in_filter": in_filter,
                            "excluded_rows": ex.tolist(), "split": "test",
                        })
                        dipakai += 1

    wl = pd.DataFrame(pairs)
    wl.insert(0, "pair_id", [f"P{i:05d}" for i in range(len(wl))])
    wl.to_parquet("data/processed/workload.parquet", index=False)

    # Kueri unik beserta provenance, dan vektornya
    q_rows = np.sort(wl["query_row"].unique())
    queries = pd.DataFrame({
        "query_id": [f"Q{r:05d}" for r in q_rows],
        "query_row": q_rows,
        "doc_id": corpus["doc_id"].to_numpy()[q_rows],
        "query_text": corpus["text"].to_numpy()[q_rows],
        "provenance": "held_out_corpus_document",
        "created_by": f"src.workload.build_queries seed={cfg['random_seed']}",
        "self_match_exclusion": ",".join(cfg["self_match_exclusion"]),
    })
    queries.to_parquet("data/processed/queries.parquet", index=False)
    np.save("data/embeddings/query_vectors.npy", vectors[q_rows])

    # Manifest workload (README bagian 42)
    frozen_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    bins = wl.groupby("bin")["pair_id"].count().to_dict()
    pd.DataFrame([{
        "workload_id": "dsic2906-1-workload-v1",
        "query_file": "data/processed/queries.parquet",
        "filter_file": "data/processed/filters.parquet",
        "n_queries": len(queries), "k": k,
        "match_rate_bins": json.dumps(bins),
        "frozen_at": frozen_at,
        "checksum_sha256": sha256("data/processed/workload.parquet"),
    }]).to_csv("data/manifests/workload_manifest.csv", index=False)

    print(f"Populasi predikat: {len(pop):,} | layak utama: {int(pop['layak_utama'].sum()):,} "
          f"| layak ekstensi: {int(pop['layak_ekstensi'].sum()):,}")
    print(f"Pasangan kueri-filter: {len(wl):,} | kueri unik: {len(queries):,}")
    print(wl.pivot_table(index="type", columns=["set", "bin"], values="pair_id", aggfunc="count", fill_value=0))


if __name__ == "__main__":
    main()
