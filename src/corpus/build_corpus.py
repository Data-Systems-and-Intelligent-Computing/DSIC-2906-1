"""Konstruksi korpus DSIC-2906-1 (Protokol bagian 16 + 17).

Menggabungkan atraksi JADESTA, desa wisata JADESTA, dan berita menjadi satu
tabel titik vektor beserta metadata alami, lalu menormalisasi penerbit dan
mengelompokkan sindikasi.

Jalankan dari root repo:
    python -m src.corpus.build_corpus

Output:
    data/processed/corpus.parquet               satu baris = satu titik vektor
    data/processed/normalization_report.csv     semua perbaikan, baris per baris
    data/processed/publisher_map.csv            domain -> publisher_id (bisa ditinjau)
    data/processed/text_length_by_source.csv    statistik panjang teks (T-03)
    data/processed/corpus_summary.json          ringkasan angka untuk laporan
    data/manifests/source_manifest.csv          checksum SHA-256 berkas mentah
    data/manifests/corpus_manifest.csv          ringkasan korpus beku
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
from datetime import datetime, timezone

import pandas as pd

from src.corpus.publishers import build_publisher_map, group_syndication
from src.utils.hashing import sha256

# Kolom wajib per titik (README bagian 10) + kolom turunan (protokol bagian 16)
CORPUS_COLUMNS = [
    "doc_id", "chunk_id", "text", "source_type", "source_id", "entity_id",
    "category", "maturity_level", "kabupaten", "province", "province_source",
    "n_kabupaten", "region_ambiguous", "publisher_domain", "publisher_id",
    "story_lineage_id", "published_at", "fetched_at", "snapshot_id",
    "source_file", "row_index", "adwi_award", "n_linked_attractions",
]


# ---------------------------------------------------------------
# 1. Manifest berkas mentah (bagian 16 langkah 1)
# ---------------------------------------------------------------
def source_manifest(files: list[str], fetched_at: dict[str, str | None]) -> tuple[pd.DataFrame, str]:
    """Hitung SHA-256 setiap berkas tanpa mengubahnya; snapshot_id = hash gabungan."""
    rows = []
    for f in sorted(files):
        st = "news" if "Berita" in os.path.basename(f) else "jadesta"
        rows.append({
            "source_type": st,
            "source_id": os.path.basename(f),
            "path_or_uri": f,
            "fetched_at": fetched_at.get(st),
            "checksum_sha256": sha256(f),
            "notes": "berkas sudah dirapikan pengumpul data (kolom provinsi, T-02)" if st == "jadesta" else "",
        })
    man = pd.DataFrame(rows)
    combined = hashlib.sha256("".join(man["checksum_sha256"]).encode()).hexdigest()
    snapshot_id = f"snap-{combined[:12]}"
    man.insert(0, "snapshot_id", snapshot_id)
    return man, snapshot_id


def news_fetched_at(news_dir: str) -> str | None:
    """Ambil waktu selesai pengumpulan dari lembar Metadata bila tersedia."""
    meta = glob.glob(os.path.join(news_dir, "*Metadata*.csv"))
    if not meta:
        return None
    m = pd.read_csv(meta[0], header=None, dtype=str)
    hit = m[m[0].astype(str).str.strip() == "Selesai dikumpulkan"]
    return None if hit.empty else str(hit.iloc[0, 1]).strip()


# ---------------------------------------------------------------
# 2. Atraksi dan desa wisata (bagian 16 langkah 2, 5, 6)
# ---------------------------------------------------------------
def _join(parts: list[str]) -> str:
    """Gabungkan potongan teks yang tidak kosong menjadi satu dokumen."""
    return " ".join(p.strip() for p in parts if isinstance(p, str) and p.strip())


def load_attractions(jd: str) -> pd.DataFrame:
    """Atraksi: kategori dari nama berkas; doc_id dari kunci kategori:id:slug."""
    frames = []
    for f in sorted(glob.glob(os.path.join(jd, "wisata_*.csv"))):
        d = pd.read_csv(f, low_memory=False).reset_index(names="row_index")
        d["source_file"] = os.path.basename(f)
        d["category"] = re.search(r"wisata_(\w+)\.csv", f).group(1)
        frames.append(d)
    a = pd.concat(frames, ignore_index=True)

    # Kunci entitas sama dengan 'Kunci atraksi' di data berita.
    # slug kosong -> pakai nomor baris agar tetap unik (dicatat di laporan).
    slug = a["slug"].where(a["slug"].notna(), "row" + a["row_index"].astype(str))
    a["entity_id"] = a["category"] + ":" + a["id"].astype(str) + ":" + slug
    a["doc_id"] = "atr:" + a["entity_id"]

    # Teks: nama + kategori + alamat + fasilitas (bagian 16 langkah 6)
    a["text"] = [
        _join([n, f"Wisata {c}.", al, f"Fasilitas: {fa}." if isinstance(fa, str) else ""])
        for n, c, al, fa in zip(a["nama"], a["category"], a["alamat"], a["fasilitas"])
    ]
    a["source_type"] = "jadesta_atraksi"
    a["source_id"] = a["url"]
    a["maturity_level"] = None
    a["adwi_award"] = None
    return a


def load_villages(jd: str) -> pd.DataFrame:
    """Desa wisata: tingkat kematangan dari nama berkas; teks ADWI tetap di kolom kategori."""
    frames = []
    for f in sorted(glob.glob(os.path.join(jd, "desa_wisata_*.csv"))):
        d = pd.read_csv(f, low_memory=False).reset_index(names="row_index")
        d["source_file"] = os.path.basename(f)
        d["maturity_level"] = re.search(r"desa_wisata_(\w+)\.csv", f).group(1)
        frames.append(d)
    v = pd.concat(frames, ignore_index=True)
    v["entity_id"] = "desa:" + v["id"].astype(str) + ":" + v["slug"].fillna("")
    v["doc_id"] = "desa:" + v["id"].astype(str)

    # Teks: nama + jenis desa wisata + alamat + fasilitas
    v["text"] = [
        _join([n, f"{j}." if isinstance(j, str) else "", al, f"Fasilitas: {fa}." if isinstance(fa, str) else ""])
        for n, j, al, fa in zip(v["nama"], v["jenis_desa_wisata"], v["alamat"], v["fasilitas"])
    ]
    v["source_type"] = "jadesta_desa"
    v["source_id"] = v["url"]
    v["category"] = "desa"
    v["adwi_award"] = v["kategori"]  # contoh: "300 Besar"
    return v


# ---------------------------------------------------------------
# 3. Berita: satu URL = satu titik (bagian 16 langkah 6, 17 butir 3)
# ---------------------------------------------------------------
_SUFFIX_SEP = re.compile(r"\s+-\s+")


def clean_title(title: str, source_name: str, domain: str) -> str:
    """Buang akhiran ' - Nama Sumber' / ' - domain' yang ditambahkan Google News."""
    t = str(title).strip()
    names = {str(source_name).strip().lower(), str(domain).strip().lower(),
             str(domain).lower().removeprefix("www.")}
    while True:
        parts = _SUFFIX_SEP.split(t)
        if len(parts) > 1 and parts[-1].strip().lower() in names:
            t = " - ".join(parts[:-1]).strip()
        else:
            return t


def load_news(nw: str) -> tuple[pd.DataFrame, list[dict]]:
    """Gabungkan 71.579 pasangan atraksi-berita menjadi URL unik dengan metadata daftar."""
    rows = pd.concat([pd.read_csv(f, low_memory=False) for f in sorted(glob.glob(os.path.join(nw, "*Berita*.csv")))],
                     ignore_index=True)
    rows["title_clean"] = [clean_title(t, s, d) for t, s, d in
                           zip(rows["Judul berita"], rows["Nama sumber"], rows["Domain sumber"])]
    rows["tgl"] = pd.to_datetime(rows["Tanggal terbit"], errors="coerce")

    def uniq(s: pd.Series) -> list:
        return sorted(s.dropna().astype(str).unique().tolist())

    g = rows.groupby("URL berita", sort=False)
    n = pd.DataFrame({
        "source_id": list(g.groups.keys()),
        "title_variants": g["Judul berita"].nunique().values,
        # Judul bersih yang paling sering muncul untuk URL itu
        "text": g["title_clean"].agg(lambda s: s.value_counts().index[0]).values,
        "published_at": g["tgl"].min().values,
        "n_dates": g["tgl"].nunique().values,
        "kabupaten": g["Kabupaten"].agg(uniq).values,
        "province": g["Provinsi"].agg(uniq).values,
        "category": g["Tipe atraksi"].agg(lambda s: uniq(s.str.lower())).values,
        "entity_id": g["Kunci atraksi"].agg(uniq).values,
        "publisher_domain": g["Domain sumber"].first().values,
        "relevance_max": g["Skor relevansi"].max().values,
    })
    n["n_linked_attractions"] = n["entity_id"].str.len()
    n["doc_id"] = ["news:" + hashlib.sha1(u.encode()).hexdigest()[:16] for u in n["source_id"]]
    n["source_type"] = "news"
    n["source_file"] = "Berita (Alam|Budaya|Buatan)"
    n["row_index"] = None
    n["maturity_level"] = None
    n["adwi_award"] = None

    # Catat perbaikan untuk laporan normalisasi
    report: list[dict] = []
    first_title = g["Judul berita"].first().values
    for doc, before, after, k in zip(n["doc_id"], first_title, n["text"], n["title_variants"]):
        if before != after or k > 1:
            report.append({"doc_id": doc, "column": "text(judul)", "before": before, "after": after,
                           "rule": f"buang akhiran ' - sumber'; pilih judul bersih terbanyak dari {k} varian"})
    for doc, k, pub in zip(n["doc_id"], n["n_dates"], n["published_at"]):
        if k > 1:
            report.append({"doc_id": doc, "column": "published_at", "before": f"{k} tanggal berbeda",
                           "after": str(pub), "rule": "ambil tanggal terbit paling awal"})
    return n, report


def syndication_review(news: pd.DataFrame) -> pd.DataFrame:
    """Kelompok sindikasi yang judulnya tidak identik, diurutkan dari paling tidak mirip.

    Untuk ditinjau manual: kemiripan judul tidak bisa membedakan, misalnya,
    'Barongsai di Mal' vs 'Barongsai di Palu'.
    """
    from rapidfuzz import fuzz
    from src.corpus.publishers import normalize_title

    rows = []
    multi = news[news.groupby("story_lineage_id")["doc_id"].transform("count") > 1]
    for sid, g in multi.groupby("story_lineage_id"):
        t = [normalize_title(x) for x in g["text"]]
        if len(set(t)) == 1:
            continue
        min_ratio = min(fuzz.ratio(a, b) for a in t for b in t if a != b)
        for _, r in g.iterrows():
            rows.append({"story_lineage_id": sid, "min_ratio": round(min_ratio, 1), "doc_id": r["doc_id"],
                         "published_at": r["published_at"], "publisher_domain": r["publisher_domain"],
                         "title": r["text"]})
    return pd.DataFrame(rows).sort_values(["min_ratio", "story_lineage_id"]) if rows else pd.DataFrame()


# ---------------------------------------------------------------
# 4. Program utama
# ---------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", default="data/raw")
    ap.add_argument("--out-dir", default="data/processed")
    ap.add_argument("--manifest-dir", default="data/manifests")
    ap.add_argument("--jadesta-fetched-at", default=None, help="waktu scraping JADESTA bila diketahui")
    ap.add_argument("--syndication-threshold", type=float, default=90.0)
    ap.add_argument("--syndication-days", type=int, default=2)
    args = ap.parse_args()

    jd, nw = os.path.join(args.raw_dir, "jadesta"), os.path.join(args.raw_dir, "news")
    os.makedirs(args.out_dir, exist_ok=True)
    os.makedirs(args.manifest_dir, exist_ok=True)

    # --- Langkah 1: manifest + snapshot_id ---
    files = glob.glob(os.path.join(jd, "*.csv")) + glob.glob(os.path.join(nw, "*Berita*.csv"))
    fetched = {"jadesta": args.jadesta_fetched_at, "news": news_fetched_at(nw)}
    man, snapshot_id = source_manifest(files, fetched)
    man.to_csv(os.path.join(args.manifest_dir, "source_manifest.csv"), index=False)

    # --- Langkah 2-6: tiga sumber ---
    atr, desa = load_attractions(jd), load_villages(jd)
    news, report = load_news(nw)

    for df in (atr, desa):
        df["province"] = df["provinsi"]
        df["n_linked_attractions"] = None
    for doc, slug, row in zip(atr["doc_id"], atr["slug"], atr["row_index"]):
        if pd.isna(slug):
            report.append({"doc_id": doc, "column": "slug", "before": "NaN", "after": f"row{row}",
                           "rule": "slug kosong -> nomor baris agar kunci entitas unik"})
    dup = atr[atr["id"].duplicated(keep=False)]
    for doc, i in zip(dup["doc_id"], dup["id"]):
        report.append({"doc_id": doc, "column": "id", "before": str(i), "after": "(tetap, tidak dihapus)",
                       "rule": "id sama dipakai atraksi berbeda; identitas memakai kategori:id:slug"})

    # --- Bagian 17: penerbit + sindikasi ---
    pmap = build_publisher_map(news["publisher_domain"])
    pmap.to_csv(os.path.join(args.out_dir, "publisher_map.csv"), index=False)
    news["publisher_id"] = news["publisher_domain"].map(dict(zip(pmap["domain"], pmap["publisher_id"])))
    news["story_lineage_id"] = group_syndication(news["text"], news["published_at"],
                                                 threshold=args.syndication_threshold,
                                                 max_days=args.syndication_days)
    syndication_review(news).to_csv(os.path.join(args.out_dir, "syndication_review.csv"), index=False)

    # --- Gabungkan menjadi satu korpus ---
    corpus = pd.concat([atr, desa, news], ignore_index=True)
    is_news = corpus["source_type"] == "news"
    # Kabupaten/provinsi berita = daftar; JADESTA = satu nilai (dibungkus daftar agar seragam)
    for col in ("kabupaten", "province", "category", "entity_id"):
        corpus[col] = [v if isinstance(v, list) else ([] if pd.isna(v) else [v]) for v in corpus[col]]
    corpus["n_kabupaten"] = corpus["kabupaten"].str.len()
    corpus["region_ambiguous"] = corpus["n_kabupaten"] > 1
    corpus["province_source"] = "kolom_provinsi_dirapikan (menunggu keputusan K-01)"
    corpus["chunk_id"] = corpus["doc_id"] + "#0"  # tanpa chunking (bagian 16 langkah 7)
    corpus["snapshot_id"] = snapshot_id
    corpus["fetched_at"] = corpus["source_type"].map(
        lambda s: fetched["news"] if s == "news" else fetched["jadesta"])
    corpus.loc[~is_news, ["publisher_domain", "publisher_id", "story_lineage_id"]] = None
    corpus["published_at"] = pd.to_datetime(corpus["published_at"])
    corpus = corpus[CORPUS_COLUMNS]

    assert corpus["doc_id"].is_unique, "doc_id harus unik"
    corpus.to_parquet(os.path.join(args.out_dir, "corpus.parquet"), index=False)

    # --- Laporan normalisasi ---
    rep = pd.DataFrame(report, columns=["doc_id", "column", "before", "after", "rule"])
    rep.to_csv(os.path.join(args.out_dir, "normalization_report.csv"), index=False)

    # --- Statistik panjang teks per source_type (T-03) ---
    lens = corpus.assign(chars=corpus["text"].str.len(), words=corpus["text"].str.split().str.len())
    tl = lens.groupby("source_type")[["chars", "words"]].describe(percentiles=[0.5]).round(1)
    tl.columns = ["_".join(c) for c in tl.columns]
    tl.to_csv(os.path.join(args.out_dir, "text_length_by_source.csv"))

    # --- Ringkasan + corpus_manifest ---
    sizes = news.groupby("story_lineage_id").size()
    summary = {
        "snapshot_id": snapshot_id,
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_documents": int(len(corpus)),
        "n_by_source": corpus["source_type"].value_counts().to_dict(),
        "n_vectors": int(len(corpus)),
        "n_entities_jadesta": int(len(atr) + len(desa)),
        "n_regions": int(pd.Series([k for ks in corpus["kabupaten"] for k in ks]).nunique()),
        "n_provinces": int(pd.Series([p for ps in corpus["province"] for p in ps]).nunique()),
        "n_categories": 4,
        "n_publisher_domains_before": int(pmap["domain"].nunique()),
        "n_publishers_after": int(pmap["publisher_id"].nunique()),
        "n_temporal_records": int(corpus["published_at"].notna().sum()),
        "news_region_ambiguous": int(corpus.loc[is_news, "region_ambiguous"].sum()),
        "news_multi_category": int((corpus.loc[is_news, "category"].str.len() > 1).sum()),
        "syndication_groups_size_gt1": int((sizes > 1).sum()),
        "news_in_syndication_groups": int(sizes[sizes > 1].sum()),
        "syndication_params": {"threshold": args.syndication_threshold, "max_days": args.syndication_days},
        "news_title_le_3_words": int((corpus.loc[is_news, "text"].str.split().str.len() <= 3).sum()),
        "normalization_report_rows": int(len(rep)),
        "max_text_chars": int(lens["chars"].max()),
    }
    with open(os.path.join(args.out_dir, "corpus_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    corpus_sha = sha256(os.path.join(args.out_dir, "corpus.parquet"))
    pd.DataFrame([{
        "corpus_id": "dsic2906-1-corpus-v1", "snapshot_id": snapshot_id,
        "n_documents": summary["n_documents"], "n_vectors": summary["n_vectors"],
        "n_entities": summary["n_entities_jadesta"], "n_regions": summary["n_regions"],
        "n_categories": summary["n_categories"], "n_publishers": summary["n_publishers_after"],
        "n_temporal_records": summary["n_temporal_records"], "checksum_sha256": corpus_sha,
    }]).to_csv(os.path.join(args.manifest_dir, "corpus_manifest.csv"), index=False)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\nStatistik panjang teks per source_type:\n", tl.to_string())


if __name__ == "__main__":
    main()
