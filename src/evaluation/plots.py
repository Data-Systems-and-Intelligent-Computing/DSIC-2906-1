"""Grafik wajib naskah utama (README bagian 40), dibuat dari tabel CSV keluaran report.py."""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib

# Backend tanpa layar, agar bisa jalan di server Lightsail
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

# Warna tetap per metode (palet yang lolos uji buta warna)
METHOD_COLOR = {"postfilter": "#2a78d6", "twohop": "#eb6834", "adaptivel": "#1baf7a"}
# Bentuk penanda berbeda per metode, agar tidak bergantung pada warna saja
METHOD_MARKER = {"postfilter": "o", "twohop": "s", "adaptivel": "^"}
METHOD_LABEL = {"postfilter": "PostFilter", "twohop": "TwoHop", "adaptivel": "AdaptiveL"}
# Urutan tetap: baseline dulu, metode yang diuji terakhir
METHOD_ORDER = ["postfilter", "twohop", "adaptivel"]


# Nilai budget/L dari teks config, untuk mengurutkan titik kurva
def _budget(config: str) -> int:
    m = re.search(r"(?:candidate_budget|L)=(\d+)", str(config))
    return int(m.group(1)) if m else 0


# Item 4 README: kurva recall@10 vs QPS untuk satu bin match rate
def recall_qps_curve(table: pd.DataFrame, bin_name: str, out: Path) -> Path:
    # Ambil baris untuk bin ini saja
    t = table[table["bin"] == bin_name].copy()
    t["budget"] = t["config"].map(_budget)
    # Satu titik per metode x konfigurasi: rata-rata lintas tipe predikat
    t = t.groupby(["method", "config", "budget"], as_index=False)[["recall_mean", "qps"]].mean()

    fig, ax = plt.subplots(figsize=(4.6, 3.4))
    for m in METHOD_ORDER:
        # Urutkan dari L/budget kecil ke besar agar garisnya tidak bolak-balik
        g = t[t["method"] == m].sort_values("budget")
        if g.empty:
            continue
        ax.plot(g["recall_mean"], g["qps"], color=METHOD_COLOR[m], marker=METHOD_MARKER[m],
                linewidth=2, markersize=6, label=METHOD_LABEL[m])

    # QPS bisa berbeda puluhan kali lipat antar-metode, jadi pakai skala log
    ax.set_yscale("log")
    # Angka QPS biasa (200, 100, 50), bukan notasi 10 pangkat
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: f"{v:g}" if f"{v:g}"[0] in "25" else ""))
    ax.set_xlabel("Recall@10")
    ax.set_ylabel("QPS (skala log)")
    ax.set_title(f"Recall–QPS, rezim {bin_name}", loc="left")
    ax.grid(True, linewidth=0.5, alpha=0.5)
    ax.legend(frameon=False, loc="best")
    # Bingkai atas dan kanan dibuang agar grafik lebih bersih
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Simpan lalu tutup gambar agar memori tidak menumpuk
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"recall_qps_{bin_name}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path

# Item 9 README: recall predikat tunggal vs majemuk, satu konfigurasi per metode
def single_vs_compound(table: pd.DataFrame, compound_types: set[str], config_per_method: dict[str, str],
                       out: Path) -> Path | None:
    # Hanya konfigurasi yang dipilih untuk tiap metode
    t = table[table["config"].isin(config_per_method.values())].copy()
    # Label jenis predikat berdasarkan tipe
    t["jenis"] = t["type"].map(lambda x: "majemuk" if x in compound_types else "tunggal")
    t = t.groupby(["bin", "method", "jenis"], as_index=False)["recall_mean"].mean()
    # Hanya bin yang memuat kedua jenis predikat (perbandingan sah, lihat Threats to Validity)
    bins = sorted(b for b, g in t.groupby("bin") if g["jenis"].nunique() == 2)
    if not bins:
        return None

    fig, axes = plt.subplots(1, len(bins), figsize=(3.2 * len(bins), 3.2), sharey=True, squeeze=False)
    for ax, b in zip(axes[0], bins):
        gb = t[t["bin"] == b]
        for i, m in enumerate(METHOD_ORDER):
            for j, jenis in enumerate(["tunggal", "majemuk"]):
                r = gb[(gb["method"] == m) & (gb["jenis"] == jenis)]
                if r.empty:
                    continue
                # Penanda penuh = tunggal, berongga = majemuk, berdampingan per metode
                ax.plot([i + (j - 0.5) * 0.36], r["recall_mean"], marker=METHOD_MARKER[m], markersize=8,
                        linestyle="none", color=METHOD_COLOR[m], markeredgewidth=2,
                        markerfacecolor=METHOD_COLOR[m] if jenis == "tunggal" else "white")
        ax.set_xticks(range(len(METHOD_ORDER)), [METHOD_LABEL[m] for m in METHOD_ORDER])
        ax.set_title(f"Rezim {b}", loc="left")
        ax.set_ylim(0, 1.05)
        ax.grid(True, linewidth=0.5, alpha=0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[0][0].set_ylabel("Recall@10")
    fig.text(0.01, -0.04, "Penanda penuh = predikat tunggal; berongga = majemuk", fontsize=8)

    out.mkdir(parents=True, exist_ok=True)
    path = out / "tunggal_vs_majemuk.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path

# Item 11 README: stabilitas overlap@k per bin dan metode, satu konfigurasi per metode
def stability_plot(table: pd.DataFrame, config_per_method: dict[str, str], out: Path) -> Path | None:
    # Grafik dilewati bila hasil stabilitas belum digabung ke tabel
    if "stability_overlap" not in table or table["stability_overlap"].isna().all():
        return None
    t = table[table["config"].isin(config_per_method.values())].dropna(subset=["stability_overlap"])
    t = t.groupby(["bin", "method"], as_index=False)["stability_overlap"].mean()
    bins = sorted(t["bin"].unique())

    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    for i, m in enumerate(METHOD_ORDER):
        g = t[t["method"] == m].set_index("bin").reindex(bins)
        # Tiap metode digeser sedikit ke kiri/kanan agar penanda tidak bertumpuk
        xs = [k + (i - 1) * 0.22 for k in range(len(bins))]
        ax.plot(xs, g["stability_overlap"], marker=METHOD_MARKER[m], markersize=7, linestyle="none",
                color=METHOD_COLOR[m], label=METHOD_LABEL[m])
    ax.set_xticks(range(len(bins)), bins)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Rezim match rate")
    ax.set_ylabel("Overlap@10 antar-ulangan")
    ax.set_title("Stabilitas kueri berulang", loc="left")
    ax.grid(True, linewidth=0.5, alpha=0.5)
    ax.legend(frameon=False, loc="lower left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    out.mkdir(parents=True, exist_ok=True)
    path = out / "stabilitas.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path