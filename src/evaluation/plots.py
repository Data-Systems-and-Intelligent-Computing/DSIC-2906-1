"""Grafik wajib naskah utama (README bagian 40), dibuat dari tabel CSV keluaran report.py."""
from __future__ import annotations

import re
import argparse
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

# Gaya sumbu yang sama untuk semua grafik
def _rapikan(ax):
    ax.grid(True, linewidth=0.5, alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# Simpan gambar lalu tutup agar memori tidak menumpuk
def _simpan(fig, out: Path, nama: str) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    path = out / nama
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


# Kurva per bin: sumbu x dan y dipilih dari kolom tabel utama, satu garis per metode (urut budget/L)
def _kurva_per_bin(table: pd.DataFrame, x: str, y: str, xlabel: str, ylabel: str, judul: str,
                   nama: str, out: Path, xlog: bool = False, ylog: bool = False) -> Path:
    t = table.assign(budget=table["config"].map(_budget))
    # Satu titik per bin x metode x konfigurasi: rata-rata lintas tipe predikat
    t = t.groupby(["bin", "method", "config", "budget"], as_index=False)[[x, y]].mean()
    bins = sorted(t["bin"].unique())
    fig, axes = plt.subplots(1, len(bins), figsize=(3.0 * len(bins), 3.1), sharey=True, squeeze=False)
    for ax, b in zip(axes[0], bins):
        for m in METHOD_ORDER:
            g = t[(t["bin"] == b) & (t["method"] == m)].sort_values("budget")
            if g.empty:
                continue
            ax.plot(g[x], g[y], color=METHOD_COLOR[m], marker=METHOD_MARKER[m], linewidth=1.8,
                    markersize=5, label=METHOD_LABEL[m])
        if xlog:
            ax.set_xscale("log")
        if ylog:
            ax.set_yscale("log")
        ax.set_title(f"Rezim {b}", loc="left")
        ax.set_xlabel(xlabel)
        _rapikan(ax)
    axes[0][0].set_ylabel(ylabel)
    axes[0][0].legend(frameon=False, loc="best", fontsize=8)
    # Judul gambar dinaikkan agar tidak menimpa judul panel pertama
    fig.suptitle(judul, x=0.01, y=1.06, ha="left")
    return _simpan(fig, out, nama)


# Item 5 README: recall@10 vs latensi p95
def recall_latency_curve(table: pd.DataFrame, out: Path) -> Path:
    return _kurva_per_bin(table, "recall_mean", "p95_ms", "Recall@10", "Latensi p95 (ms, implementasi Python)",
                          "Recall–latensi p95", "recall_p95.png", out)


# Biaya bebas implementasi (Bab 2 subbab 2.10): recall vs median perhitungan jarak (D) dan evaluasi predikat (E)
def recall_cost_curves(table: pd.DataFrame, out: Path) -> list[Path]:
    paths = [_kurva_per_bin(table, "dist_comp_median", "recall_mean", "Median perhitungan jarak (D, log)",
                            "Recall@10", "Recall terhadap perhitungan jarak", "recall_biaya_D.png", out, xlog=True)]
    paths.append(_kurva_per_bin(table, "pred_eval_median", "recall_mean", "Median evaluasi predikat (E, log)",
                                "Recall@10", "Recall terhadap evaluasi predikat", "recall_biaya_E.png", out,
                                xlog=True))
    return paths


# Item 6 dan 7 README: recall dan titik dikunjungi menurut match rate aktual (budget/L terbesar tiap metode)
def match_rate_plots(per_mr: pd.DataFrame, config_per_method: dict[str, str], out: Path) -> list[Path]:
    t = per_mr[per_mr["config"].isin(config_per_method.values())]
    paths = []
    for kolom, label, nama, ylog in [("recall_mean", "Recall@10", "match_rate_recall.png", False),
                                     ("visited_median", "Median titik dikunjungi (log)",
                                      "match_rate_visited.png", True)]:
        fig, ax = plt.subplots(figsize=(4.6, 3.3))
        for m in METHOD_ORDER:
            g = t[t["method"] == m].sort_values("match_rate_median")
            if g.empty:
                continue
            ax.plot(g["match_rate_median"] * 100, g[kolom], color=METHOD_COLOR[m], marker=METHOD_MARKER[m],
                    linewidth=1.8, markersize=5, label=METHOD_LABEL[m])
        ax.set_xscale("log")
        if ylog:
            ax.set_yscale("log")
        ax.set_xlabel("Match rate (% , log; median kelompok kuantil)")
        ax.set_ylabel(label)
        ax.set_title(f"{label.split(' (')[0]} menurut match rate", loc="left")
        ax.legend(frameon=False, loc="best", fontsize=8)
        _rapikan(ax)
        paths.append(_simpan(fig, out, nama))
    return paths


# P3: taksiran ŝp AdaptiveL terhadap match rate aktual (konfigurasi L terbesar); ŝp = 0 digambar di pita bawah
def sp_hat_vs_match_rate(sp: pd.DataFrame, config: str, n_sample: int, out: Path) -> Path | None:
    t = sp[sp["config"] == config].dropna(subset=["sp_hat"])
    if t.empty:
        return None
    lantai = 1 / (2 * n_sample)
    fig, ax = plt.subplots(figsize=(4.8, 3.6))
    for dalam, mk, lab in [(True, "o", "kueri di dalam filter"), (False, "x", "kueri di luar filter")]:
        g = t[t["query_in_filter"] == dalam] if "query_in_filter" in t else t
        y = g["sp_hat"].where(g["sp_hat"] > 0, lantai)
        ax.scatter(g["match_rate"], y, s=9, marker=mk, alpha=0.45, color=METHOD_COLOR["adaptivel"] if dalam else "#555555",
                   label=lab, linewidths=0.8)
    lo = min(t["match_rate"].min(), lantai)
    ax.plot([lo, 1], [lo, 1], color="#999999", linewidth=1, linestyle="--", label="ŝp = match rate")
    ax.axhline(1 / n_sample, color="#bbbbbb", linewidth=0.8, linestyle=":")
    ax.text(lo, 1 / n_sample * 1.15, f"resolusi 1/{n_sample}", fontsize=7, color="#777777")
    ax.text(lo, lantai * 1.15, "ŝp = 0", fontsize=7, color="#777777")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Match rate aktual (log)")
    ax.set_ylabel("Taksiran ŝp (log)")
    ax.set_title("Taksiran match rate AdaptiveL", loc="left")
    ax.legend(frameon=False, fontsize=7, loc="lower right")
    _rapikan(ax)
    return _simpan(fig, out, "sp_hat_vs_match_rate.png")


def main() -> None:
    import yaml

    ap = argparse.ArgumentParser()
    ap.add_argument("--report-dir", required=True, help="folder keluaran src.evaluation.report")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    # Tabel utama yang sama dengan yang dilaporkan, agar angka grafik = angka tabel
    table = pd.read_csv(Path(args.report_dir) / "main_table.csv")
    # Daftar tipe predikat majemuk diambil dari konfigurasi workload beku
    tipe = yaml.safe_load(Path("configs/workload.yaml").read_text(encoding="utf-8"))["predicate_types"]
    # Grafik tunggal/majemuk dan stabilitas memakai budget/L terbesar tiap metode
    t = table.assign(budget=table["config"].map(_budget))
    cpm = {m: g.sort_values("budget")["config"].iloc[-1] for m, g in t.groupby("method")}

    out = Path(args.out_dir)
    paths = [recall_qps_curve(table, b, out) for b in sorted(table["bin"].unique())]
    paths += [single_vs_compound(table, set(tipe["compound"]), cpm, out), stability_plot(table, cpm, out)]
    paths.append(recall_latency_curve(table, out))
    # Grafik biaya D/E hanya bila kolom D tersedia (laporan lama tidak memilikinya)
    if "dist_comp_median" in table:
        paths += recall_cost_curves(table, out)
    per_mr_path = Path(args.report_dir) / "per_match_rate.csv"
    if per_mr_path.exists():
        paths += match_rate_plots(pd.read_csv(per_mr_path), cpm, out)
    sp_path = Path(args.report_dir) / "adaptivel_sp_hat.csv"
    if sp_path.exists() and "adaptivel" in cpm:
        n_sample = int(re.search(r"n_sample=(\d+)", cpm["adaptivel"]).group(1))
        paths.append(sp_hat_vs_match_rate(pd.read_csv(sp_path), cpm["adaptivel"], n_sample, out))
    for p in paths:
        if p is not None:
            print(p)


if __name__ == "__main__":
    main()