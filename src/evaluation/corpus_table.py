"""Tabel statistik korpus dan metadata (README bagian 11 dan bagian 40 item 1).

Angka diambil dari artefak beku (corpus_summary.json, text_length_by_source.csv, corpus.parquet),
bukan dihitung ulang dari data mentah, agar sama dengan korpus yang dipakai benchmark.

Jalankan dari root repo:
    python -m src.evaluation.corpus_table --out-dir results/summary/corpus_2026-11-15
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

PROCESSED = Path("data/processed")


def corpus_stats(summary: dict, corpus: pd.DataFrame) -> pd.DataFrame:
    # Rentang tanggal terbit berita (rekaman temporal)
    tgl = corpus["published_at"].dropna()
    baris = [
        # Ukuran korpus (README bagian 11)
        ("Dokumen", summary["n_documents"], "seluruh sumber"),
        ("Titik vektor", summary["n_vectors"], "satu vektor per dokumen, tanpa chunking"),
        ("Dokumen atraksi JADESTA", summary["n_by_source"]["jadesta_atraksi"], "source_type = jadesta_atraksi"),
        ("Dokumen desa wisata JADESTA", summary["n_by_source"]["jadesta_desa"], "source_type = jadesta_desa"),
        ("Dokumen berita (judul)", summary["n_by_source"]["news"], "source_type = news"),
        ("Entitas JADESTA", summary["n_entities_jadesta"], "atraksi + desa wisata"),
        # Kardinalitas metadata
        ("Kabupaten/kota", summary["n_regions"], "predikat wilayah tingkat kabupaten"),
        ("Provinsi", summary["n_provinces"], "diturunkan dari kabupaten (Kepmendagri 2025, K-01)"),
        ("Kategori", summary["n_categories"], "alam, budaya, buatan, desa"),
        ("Tipe sumber", len(summary["n_by_source"]), "tanpa Wikipedia/Wikidata (K-03)"),
        ("Domain penerbit sebelum normalisasi", summary["n_publisher_domains_before"], "domain mentah"),
        ("Penerbit setelah normalisasi", summary["n_publishers_after"], "subdomain satu penerbit digabung"),
        ("Rekaman temporal", summary["n_temporal_records"],
         f"tanggal terbit berita {tgl.min():%Y-%m-%d} s.d. {tgl.max():%Y-%m-%d}"),
        # Kualitas metadata dan duplikasi
        ("Berita dengan wilayah ambigu", summary["news_region_ambiguous"], "lebih dari satu kabupaten (DT-3)"),
        ("Berita dengan lebih dari satu kategori", summary["news_multi_category"], ""),
        ("Kelompok sindikasi (ukuran > 1)", summary["syndication_groups_size_gt1"],
         f"ambang kemiripan {summary['syndication_params']['threshold']}, "
         f"rentang {summary['syndication_params']['max_days']} hari"),
        ("Berita di dalam kelompok sindikasi", summary["news_in_syndication_groups"], "disimpan, tidak dibuang"),
    ]
    return pd.DataFrame(baris, columns=["statistik", "nilai", "keterangan"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    summary = json.loads((PROCESSED / "corpus_summary.json").read_text(encoding="utf-8"))
    corpus = pd.read_parquet(PROCESSED / "corpus.parquet", columns=["published_at"])
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    stats = corpus_stats(summary, corpus)
    stats.to_csv(out / "corpus_stats.csv", index=False)
    # Statistik panjang teks per tipe sumber (T-03 / K-02), disalin apa adanya
    pd.read_csv(PROCESSED / "text_length_by_source.csv").to_csv(out / "text_length_by_source.csv", index=False)
    (out / "_meta.json").write_text(json.dumps({"snapshot_id": summary["snapshot_id"],
                                                "corpus_built_at": summary["built_at"]}, indent=2),
                                    encoding="utf-8")
    print(stats.to_string(index=False))


if __name__ == "__main__":
    main()
