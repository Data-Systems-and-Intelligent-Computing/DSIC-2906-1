"""
ringkasan_bimbingan.py
Menampilkan angka-angka utama progres DSIC-2906-1 langsung dari artefak di repo,
untuk ditunjukkan saat bimbingan. Hanya membaca, tidak mengubah berkas apa pun.

Jalankan dari root repo:  python scripts/ringkasan_bimbingan.py [bagian] [--csv DIR]
bagian (opsional): workload | dt4 | p3 | p11 | p4 | robust | templat | sindikasi

Dengan --csv DIR, setiap tabel ringkasan juga ditulis sebagai CSV kecil ke DIR
(misalnya results/summary/), beserta _meta.json berisi SHA-256 berkas JSONL sumber,
commit repo saat ringkasan dibuat, dan catatan provenance run (--catatan-run).
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

pd.set_option("display.width", 200)
# Argumen: bagian (posisional, opsional), --csv DIR, --catatan-run TEKS
_args = sys.argv[1:]
CSV_DIR = None
CATATAN_RUN = ""
if "--csv" in _args:
    i = _args.index("--csv")
    CSV_DIR = Path(_args[i + 1])
    del _args[i:i + 2]
if "--catatan-run" in _args:
    i = _args.index("--catatan-run")
    CATATAN_RUN = _args[i + 1]
    del _args[i:i + 2]
bagian = _args[0] if _args else "semua"
_ditulis = []


# Menampilkan tabel ke layar dan, bila --csv dipakai, menyimpannya sebagai CSV
def tampil(nama, df):
    print(df.to_string())
    if CSV_DIR is not None:
        CSV_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(CSV_DIR / f"{nama}.csv")
        _ditulis.append(f"{nama}.csv")


# SHA-256 berkas sumber untuk metadata
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


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
    tampil("workload_per_set_bin", t.round(3))

d = None
if bagian in ("semua", "dt4", "p3", "p11", "p4"):
    d = baca("results/raw/dev_benchmark.jsonl")

# DT-4: AdaptiveL vs PostFilter dengan budget setara L x m_max
if bagian in ("semua", "dt4"):
    judul("2. DT-4: RECALL@10 RATA-RATA (dev benchmark, 100 kueri)")
    kolom = ["PF400", "PF3200", "AL400", "TH400"]
    x = d[d.c.isin(kolom)].groupby(["bin", "c"])
    tampil("dt4_recall_at_10_mean", x.recall_at_10.mean().unstack()[kolom].round(3))
    print("\nPerbandingan jarak (median):")
    tampil("dt4_distance_comparisons_median", x.distance_comparisons.median().unstack()[kolom].round(0))

# P3: distribusi estimasi sp_hat dan pengali AdaptiveL
if bagian in ("semua", "p3"):
    judul("3. P3: ESTIMASI sp_hat AdaptiveL (n_sample 32, m_max 8)")
    a = d[(d.method == "adaptivel") & (d.n_sample == 32) & (d.m_max == 8)]
    p3 = a.groupby("bin").agg(match_rate_median=("match_rate", "median"),
                               pct_sp_hat_nol=("sp_hat", lambda s: (s == 0).mean()),
                               pct_pengali_maks=("multiplier", lambda s: (s >= 8).mean())).round(3)
    tampil("p3_sp_hat_multiplier_per_bin", p3)

# P11: rasio titik dikunjungi terhadap L
if bagian in ("semua", "p11"):
    judul("4. P11: RASIO |V|/L (median)")
    v = d[d.method != "postfilter"].copy()
    v["rasio"] = v.visited_nodes / v.L
    tampil("p11_visited_over_L_median", v.groupby(["bin", "method"]).rasio.median().unstack().round(2))

# P4: evaluasi predikat TwoHop total vs unik
if bagian in ("semua", "p4"):
    judul("5. P4: EVALUASI PREDIKAT TwoHop (median)")
    t = d[d.method == "twohop"]
    tampil("p4_twohop_predicate_evaluations_median", t.groupby("bin")[["distance_comparisons", "predicate_evaluations",
                                                                     "predicate_evaluations_unique"]].median())

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
    tampil("robust_dt3_any_vs_tanpa_ambigu", g.round(3))

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


# Metadata provenance ringkasan CSV
if CSV_DIR is not None and _ditulis:
    def _git(*a):
        try:
            return subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout.strip()
        except Exception:
            return None
    sumber = {}
    for p in ("results/raw/dev_benchmark.jsonl", "results/raw/dev_benchmark_robust.jsonl"):
        if Path(p).is_file() and p in _cache:
            sumber[p] = {"sha256": sha256(p), "n_baris": int(len(_cache[p])),
                         "diubah_utc": datetime.fromtimestamp(Path(p).stat().st_mtime, timezone.utc)
                         .isoformat(timespec="seconds")}
    meta = {
        "dibuat_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dibuat_oleh": "scripts/ringkasan_bimbingan.py " + " ".join(sys.argv[1:]),
        "commit_repo_saat_ringkasan": _git("rev-parse", "--short", "HEAD"),
        "working_tree_bersih": _git("status", "--porcelain") == "",
        "workload_manifest": pd.read_csv("data/manifests/workload_manifest.csv").iloc[0].to_dict()
        if Path("data/manifests/workload_manifest.csv").is_file() else None,
        "sumber_jsonl": sumber,
        "catatan_run": CATATAN_RUN,
        "berkas_csv": sorted(_ditulis),
    }
    (CSV_DIR / "_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str),
                                        encoding="utf-8")
    print(f"\nCSV ringkasan ditulis ke {CSV_DIR}/ ({len(_ditulis)} berkas + _meta.json)")
