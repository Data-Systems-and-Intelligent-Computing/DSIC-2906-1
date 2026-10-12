"""Verifikasi audit korpus (Protokol DSIC-2906-1 bagian 3-6, 8, 10, 22).

Script ini hanya MEMBACA data mentah, tidak mengubah apa pun.
Jalankan dari root repo:  python -m src.corpus.audit
"""
from __future__ import annotations

import argparse
import glob
import os

import pandas as pd


# ---------------------------------------------------------------
# 1. Pembacaan data mentah
# ---------------------------------------------------------------
def load_raw(raw_dir: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Baca atraksi, desa, dan berita (baris mentah + URL unik)."""
    jd = os.path.join(raw_dir, "jadesta")
    nw = os.path.join(raw_dir, "news")

    # Atraksi: wisata_alam / wisata_budaya / wisata_buatan
    atr_files = sorted(glob.glob(os.path.join(jd, "wisata_*.csv")))
    atr = pd.concat(
        [pd.read_csv(f, low_memory=False).assign(source_file=os.path.basename(f)) for f in atr_files],
        ignore_index=True,
    )
    # Kategori diturunkan dari nama berkas (alam | budaya | buatan)
    atr["category"] = atr["source_file"].str.extract(r"wisata_(\w+)\.csv")[0]

    # Desa wisata: rintisan / berkembang / maju / mandiri
    desa_files = sorted(glob.glob(os.path.join(jd, "desa_wisata_*.csv")))
    desa = pd.concat(
        [pd.read_csv(f, low_memory=False).assign(source_file=os.path.basename(f)) for f in desa_files],
        ignore_index=True,
    )
    # Tingkat kematangan diturunkan dari nama berkas
    desa["maturity_level"] = desa["source_file"].str.extract(r"desa_wisata_(\w+)\.csv")[0]

    # Berita: tiga sheet Berita (Alam, Budaya, Buatan) yang sudah diekspor ke CSV
    news_files = sorted(glob.glob(os.path.join(nw, "*Berita*.csv")))
    news_rows = pd.concat([pd.read_csv(f, low_memory=False) for f in news_files], ignore_index=True)
    news = news_rows.drop_duplicates(subset=["URL berita"]).copy()

    if atr.empty or desa.empty or news.empty:
        raise SystemExit(f"Data tidak lengkap di {raw_dir}: cek folder jadesta/ dan news/")
    return atr, desa, news_rows, news


def pct(n: float, total: float) -> str:
    return f"{100 * n / total:.4f}%"


# ---------------------------------------------------------------
# 2. Audit
# ---------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", default="data/raw")
    args = ap.parse_args()

    atr, desa, news_rows, news = load_raw(args.raw_dir)
    N = len(atr) + len(desa) + len(news)

    # --- Bagian 3: komposisi korpus ---
    print("=== [3] Komposisi korpus ===")
    print(f"Atraksi JADESTA      : {len(atr):>7,}  (id unik {atr['id'].nunique():,}, "
          f"duplikat {len(atr) - atr['id'].nunique()})")
    print(f"Desa wisata JADESTA  : {len(desa):>7,}")
    print(f"Berita (URL unik)    : {len(news):>7,}  (dari {len(news_rows):,} pasangan atraksi-berita)")
    print(f"TOTAL titik          : {N:>7,}   [protokol: 64.354]")

    # --- Bagian 4: kardinalitas metadata ---
    kab = pd.concat([atr["kabupaten"], desa["kabupaten"], news["Kabupaten"]]).dropna()
    rc = kab.value_counts()
    print("\n=== [4] Kardinalitas metadata ===")
    print(f"Wilayah (kabupaten)  : {len(rc):,}   [protokol: 483]")
    print(f"Kategori atraksi     : {atr['category'].nunique()}  {sorted(atr['category'].unique())}")
    print(f"Tingkat kematangan   : {desa['maturity_level'].nunique()}  {sorted(desa['maturity_level'].unique())}")
    print(f"Penerbit (domain)    : {news['Domain sumber'].nunique():,}   [protokol: 3.862]")

    # --- Bagian 5.1: match rate predikat tunggal ---
    print("\n=== [5.1] Match rate tipe sumber & kategori ===")
    for name, n in [("news", len(news)), ("jadesta_atraksi", len(atr)), ("jadesta_desa", len(desa))]:
        print(f"  source_type={name:<16} {n:>7,}  {pct(n, N)}")
    # Kategori: atraksi + berita mewarisi tipe atraksinya; desa = 'desa'
    cat = pd.concat([atr["category"], news["Tipe atraksi"].str.lower()]).value_counts()
    for name, n in cat.items():
        print(f"  category={name:<19} {n:>7,}  {pct(n, N)}")
    print(f"  category={'desa':<19} {len(desa):>7,}  {pct(len(desa), N)}")

    print("\n=== [5.1] Match rate wilayah (kabupaten) ===")
    mr = 100 * rc / N
    print(f"min {mr.min():.4f}%  median {mr.median():.4f}%  maks {mr.max():.3f}%"
          f"   [protokol: 0,0016 / 0,1010 / 2,085]")
    bins = [0, 0.01, 0.10, 0.50, 1.00, 5.00, 100]
    labels = ["0,00-0,01%", "0,01-0,10%", "0,10-0,50%", "0,50-1,00%", "1,00-5,00%", ">5,00%"]
    print(pd.cut(mr, bins=bins, labels=labels, include_lowest=True).value_counts().sort_index().to_string())

    print("\n=== [5.1] Match rate temporal (berita) ===")
    tgl = pd.to_datetime(news["Tanggal terbit"], errors="coerce")
    print(f"  tanggal tidak valid/kosong: {tgl.isna().sum():,}")
    for t in ["2021-09-01", "2024-01-01", "2025-01-01", "2026-01-01", "2026-07-23"]:
        n = int((tgl >= t).sum())
        print(f"  sejak {t}: {n:>7,}  {pct(n, N)}")

    # --- Bagian 6: kelayakan top-k ---
    print("\n=== [6] Kelayakan top-k (wilayah) ===")
    for thr in [10, 50, 100]:
        print(f"  >= {thr:>3} titik: {int((rc >= thr).sum()):>4} dari {len(rc)}")

    # --- Bagian 8 (T-02): kerusakan kolom provinsi ---
    print("\n=== [8] T-02 kolom provinsi ===")
    pola = r"^\d+ Besar ADWI \d{4}$"
    for f, g in desa.groupby("source_file"):
        m = g["provinsi"].astype(str).str.strip().str.match(pola)
        print(f"  {f:<30} teks ADWI: {int(m.sum()):>4} / {len(g):,}")
    m_all = desa["provinsi"].astype(str).str.strip().str.match(pola)
    print(f"  TOTAL desa                     teks ADWI: {int(m_all.sum()):>4} / {len(desa):,}   [protokol: 1.175]")
    print(f"  provinsi terisi pada atraksi : {int(atr['provinsi'].notna().sum()):,} / {len(atr):,}   [protokol: 0]")

    # --- Bagian 10 (T-04): penerbit ---
    print("\n=== [10] T-04 penerbit & sindikasi ===")
    vc = news["Domain sumber"].value_counts()
    print(f"  domain >= 50 artikel : {int((vc >= 50).sum())}   [protokol: 122]")
    print(f"  domain >= 100 artikel: {int((vc >= 100).sum())}   [protokol: 39]")
    print(f"  domain terbesar      : {vc.index[0]} {pct(vc.iloc[0], N)}   [protokol: 2,78%]")
    detik = news_rows[news_rows["Domain sumber"].str.contains("detik", na=False)]
    print(f"  subdomain detik      : {detik['Domain sumber'].nunique()} subdomain, "
          f"{len(detik):,} baris ({100 * len(detik) / len(news_rows):.1f}% baris berita)   [protokol: 4 / 8.901 / 12,4%]")


if __name__ == "__main__":
    main()
