"""Normalisasi penerbit dan pengelompokan sindikasi berita (Protokol bagian 17)."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
import tldextract
from rapidfuzz import fuzz, process

# PSL bawaan paket (tanpa unduh) agar hasil reprodusibel;
# domain privat (blogspot.com, dll.) diperlakukan sebagai suffix sehingga
# blog berbeda tidak tergabung menjadi satu penerbit.
_EXTRACT = tldextract.TLDExtract(suffix_list_urls=(), include_psl_private_domains=True)


# ---------------------------------------------------------------
# 1. Domain -> publisher_id (bagian 17 butir 1)
# ---------------------------------------------------------------
def publisher_id(domain: str) -> str:
    """Satukan subdomain satu penerbit: travel.detik.com -> detik.com."""
    d = str(domain).strip().lower()
    r = _EXTRACT(d)
    reg = getattr(r, "top_domain_under_public_suffix", None) or r.registered_domain
    return reg or d  # domain tanpa suffix dikenal: pakai apa adanya


def build_publisher_map(domains: pd.Series) -> pd.DataFrame:
    """Tabel pemetaan yang bisa ditinjau manusia: domain, publisher_id, jumlah artikel."""
    counts = domains.value_counts()
    m = pd.DataFrame({"domain": counts.index, "n_articles": counts.values})
    m["publisher_id"] = m["domain"].map(publisher_id)
    m["n_domains_in_publisher"] = m.groupby("publisher_id")["domain"].transform("count")
    return m.sort_values(["n_domains_in_publisher", "publisher_id", "n_articles"],
                         ascending=[False, True, False]).reset_index(drop=True)


# ---------------------------------------------------------------
# 2. Sindikasi: judul mirip + tanggal berdekatan (bagian 17 butir 2)
# ---------------------------------------------------------------
def normalize_title(t: str) -> str:
    """Huruf kecil, buang tanda baca, rapikan spasi."""
    t = re.sub(r"[^\w\s]", " ", str(t).lower())
    return re.sub(r"\s+", " ", t).strip()


class _UnionFind:
    def __init__(self, n: int):
        self.p = list(range(n))

    def find(self, i: int) -> int:
        while self.p[i] != i:
            self.p[i] = self.p[self.p[i]]
            i = self.p[i]
        return i

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def group_syndication(titles: pd.Series, dates: pd.Series, threshold: float = 90.0,
                      max_days: int = 2) -> list[str]:
    """Beri story_lineage_id per kelompok; semua anggota tetap disimpan.

    Dua berita satu kelompok bila kemiripan judul ternormalisasi >= threshold
    (rapidfuzz ratio, 0-100) dan selisih tanggal terbit <= max_days hari.
    Berita tanpa tanggal hanya digabung bila judulnya identik.
    """
    norm = [normalize_title(t) for t in titles]
    dts = pd.to_datetime(pd.Series(dates).reset_index(drop=True))
    n = len(norm)
    uf = _UnionFind(n)

    # (a) Judul identik setelah normalisasi
    first: dict[str, int] = {}
    for i, t in enumerate(norm):
        if t in first and (pd.isna(dts[i]) or pd.isna(dts[first[t]])
                           or abs((dts[i] - dts[first[t]]).days) <= max_days):
            uf.union(i, first[t])
        first.setdefault(t, i)

    # (b) Judul mirip dalam jendela tanggal: bandingkan hari d dengan hari d..d+max_days
    day = dts.dt.floor("D")
    by_day = {d: np.flatnonzero((day == d).values) for d in day.dropna().unique()}
    for d, idx in by_day.items():
        win = np.concatenate([by_day.get(d + pd.Timedelta(days=k), np.array([], int))
                              for k in range(max_days + 1)])
        if len(win) < 2:
            continue
        sim = process.cdist([norm[i] for i in idx], [norm[j] for j in win],
                            scorer=fuzz.ratio, score_cutoff=threshold, workers=-1)
        for a, b in zip(*np.nonzero(sim)):
            i, j = idx[a], win[b]
            if i != j:
                uf.union(int(i), int(j))

    return [f"story-{uf.find(i):06d}" for i in range(n)]
