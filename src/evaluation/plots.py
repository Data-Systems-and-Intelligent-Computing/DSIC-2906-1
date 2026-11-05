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