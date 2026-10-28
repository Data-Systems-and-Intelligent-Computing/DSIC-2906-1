"""
ringkasan_bimbingan.py
Menampilkan angka-angka utama progres DSIC-2906-1 langsung dari artefak di repo,
untuk ditunjukkan saat bimbingan. Hanya membaca, tidak mengubah berkas apa pun.

Jalankan dari root repo:  python scripts/ringkasan_bimbingan.py [bagian]
bagian (opsional): workload | dt4 | p3 | p11 | p4 | robust | templat | sindikasi
"""
import sys

import pandas as pd

pd.set_option("display.width", 200)
bagian = sys.argv[1] if len(sys.argv) > 1 else "semua"


# Judul bagian agar keluaran mudah dibaca di layar
def judul(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# Label konfigurasi ringkas (sekaligus untuk seluruh kolom, bukan per baris):
# PF = PostFilter, TH = TwoHop, AL = AdaptiveL (n_sample 32, m_max 8)
def label_cfg(df):
    budget = df["candidate_budget"].fillna(0).astype(int).astype(str)
    L = df["L"].fillna(0).astype(int).astype(str)
    lab = pd.Series(None, index=df.index, dtype=object)
    lab[df.method == "postfilter"] = "PF" + budget
    lab[df.method == "twohop"] = "TH" + L
    al = (df.method == "adaptivel") & (df.n_sample == 32) & (df.m_max == 8)
    lab[al] = "AL" + L
    return lab


# Pembacaan hasil benchmark sekali saja (berkas JSONL besar)
_cache = {}


def baca(path):
    if path not in _cache:
        df = pd.read_json(path, lines=True)
        df["c"] = label_cfg(df)
        _cache[path] = df
    return _cache[path]


# Workload beku: manifest dan sebaran pasangan per set x bin
if bagian in ("semua", "workload"):
    judul("1. WORKLOAD BEKU (P2, DT-1, DT-2)")
    m = pd.read_csv("data/manifests/workload_manifest.csv")
    print(m[["workload_id", "n_queries", "frozen_at"]].to_string(index=False))
    print("checksum:", m.checksum_sha256.iloc[0][:16], "...")
    w = pd.read_parquet("data/processed/workload.parquet")
    t = w.groupby(["set", "bin"]).agg(pasangan=("pair_id", "size"), mr_median_pct=("match_rate", "median"),
                                      mr_min_pct=("match_rate", "min"), mr_max_pct=("match_rate", "max"),
                                      eligible_min=("n_eligible", "min"))
    t[["mr_median_pct", "mr_min_pct", "mr_max_pct"]] *= 100
    print(t.round(3).to_string())

d = None
if bagian in ("semua", "dt4", "p3", "p11", "p4"):
    d = baca("results/raw/dev_benchmark.jsonl")

# DT-4: AdaptiveL vs PostFilter dengan budget setara L x m_max
if bagian in ("semua", "dt4"):
    judul("2. DT-4: RECALL@10 RATA-RATA (dev benchmark, 100 kueri)")
    kolom = ["PF400", "PF3200", "AL400", "TH400"]
    x = d[d.c.isin(kolom)].groupby(["bin", "c"])
    print(x.recall_at_10.mean().unstack()[kolom].round(3).to_string())
    print("\nPerbandingan jarak (median):")
    print(x.distance_comparisons.median().unstack()[kolom].round(0).to_string())

# P3: distribusi estimasi sp_hat dan pengali AdaptiveL
if bagian in ("semua", "p3"):
    judul("3. P3: ESTIMASI sp_hat AdaptiveL (n_sample 32, m_max 8)")
    a = d[(d.method == "adaptivel") & (d.n_sample == 32) & (d.m_max == 8)]
    print(a.groupby("bin").agg(match_rate_median=("match_rate", "median"),
                               pct_sp_hat_nol=("sp_hat", lambda s: (s == 0).mean()),
                               pct_pengali_maks=("multiplier", lambda s: (s >= 8).mean())).round(3).to_string())

# P11: rasio titik dikunjungi terhadap L
if bagian in ("semua", "p11"):
    judul("4. P11: RASIO |V|/L (median)")
    v = d[d.method != "postfilter"].copy()
    v["rasio"] = v.visited_nodes / v.L
    print(v.groupby(["bin", "method"]).rasio.median().unstack().round(2).to_string())

# P4: evaluasi predikat TwoHop total vs unik
if bagian in ("semua", "p4"):
    judul("5. P4: EVALUASI PREDIKAT TwoHop (median)")
    t = d[d.method == "twohop"]
    print(t.groupby("bin")[["distance_comparisons", "predicate_evaluations",
                            "predicate_evaluations_unique"]].median().to_string())

# Robustness DT-3: dengan vs tanpa berita ambigu
if bagian in ("semua", "robust"):
    judul("6. ROBUSTNESS DT-3: RECALL any_match -> tanpa berita ambigu")
    a = baca("results/raw/dev_benchmark.jsonl")
    b = baca("results/raw/dev_benchmark_robust.jsonl")
    a = a[a.filter_id.isin(b.filter_id.unique())]
    kolom = ["PF400", "TH400", "AL400"]
    ra = a[a.c.isin(kolom)].groupby(["filter_id", "c"]).agg(mr=("match_rate", "first"), rec=("recall_at_10", "mean"))
    rb = b[b.c.isin(kolom)].groupby(["filter_id", "c"]).agg(mr=("match_rate", "first"), rec=("recall_at_10", "mean"))
    g = ra.join(rb, lsuffix="_any", rsuffix="_tanpa")
    g[["mr_any", "mr_tanpa"]] *= 100
    print(g.round(3).to_string())

# Efek templat teks JADESTA (ancaman validitas)
if bagian in ("semua", "templat"):
    judul("7. EFEK TEMPLAT TEKS (cosine tetangga terdekat)")
    print(pd.read_csv("data/reports/template_effect.csv").to_string(index=False))

# Tinjauan manual sindikasi (No 34)
if bagian in ("semua", "sindikasi"):
    judul("8. TINJAUAN SINDIKASI (No 34)")
    s = pd.read_csv("data/reports/syndication_review_labeled.csv", keep_default_na=False)
    k = s.groupby("story_lineage_id").agg(label=("label", "first"), catatan=("catatan", "first"))
    print(k.label.value_counts().to_string())
    print("\nKelompok salah:")
    print(k[k.label == "salah"].catatan.to_string())
