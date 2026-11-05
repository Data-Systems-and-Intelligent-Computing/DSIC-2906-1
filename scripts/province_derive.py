"""Penurunan provinsi dari kabupaten/kota (K-01 / DL-10) dan laporan selisih
terhadap kolom provinsi yang dipakai workload v1.

Derives province from kabupaten/kota via the committed Kepmendagri reference
table, compares it with the province column used by workload v1, and reports
which province filters change.

Masukan:
- data/reference/kab_prov_kepmendagri_2025.csv  (tabel referensi resmi)
- data/processed/corpus.parquet                 (kolom kabupaten & province v1, berbentuk list)
- data/processed/filters.parquet                (filter beku v1, termasuk n_eligible)
- data/_asli/data-jadesta/*.csv dan data/raw/jadesta/*.csv (pemeriksaan modifikasi berkas)
- opsional: data/reference/kabupaten_alias.csv  (nama_jadesta,kode_kab,alasan) untuk nama
  lama/ejaan lain yang sudah ditinjau manual; tanpa berkas ini tidak ada pencocokan selain
  nama resmi.

Keluaran (di data/reports/):
- province_derivation_jadesta.csv : SEMUA baris JADESTA, v1 vs turunan, jenis selisih
- province_unmapped_kabupaten.csv : nama kabupaten yang tidak terpetakan (semua sumber)
- province_filter_impact.csv      : filter yang memuat provinsi, n_eligible v1 vs turunan
- raw_vs_asli_column_diff.csv     : jumlah sel yang berbeda antara raw/ dan _asli/ per kolom
- province_derivation_summary.json: ringkasan seluruh angka di atas

Aturan:
- Provinsi hanya diisi bila kabupaten cocok dengan tabel referensi (atau alias yang ditinjau).
- Kabupaten kosong -> "tak_terpetakan_kabupaten_kosong"; tidak pernah diisi dari kolom lain.
- Perbandingan memakai kode provinsi, sehingga perbedaan ejaan nama bukan selisih.

Pemakaian (dari root repo):
    python scripts/province_derive.py
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

# Root repo dimasukkan ke sys.path agar modul src bisa diimpor saat skrip dijalankan langsung
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.corpus.province_map import (  # noqa: E402
    ST_AMBIGU, ST_TIDAK_DIKENAL, ProvinceMapper, as_list,
)


def jenis_selisih(v1_codes: set, v1_unknown: list, der_codes: set) -> str:
    # Klasifikasi selisih per baris berdasarkan kode provinsi
    if v1_unknown:
        return "v1_nama_provinsi_tidak_dikenal"
    if not v1_codes and not der_codes:
        return "keduanya_kosong"
    if v1_codes and not der_codes:
        return "v1_terisi_turunan_kosong"
    if not v1_codes and der_codes:
        return "v1_kosong_turunan_terisi"
    return "sama" if v1_codes == der_codes else "beda_provinsi"


def raw_vs_asli(asli_dir: Path, raw_dir: Path) -> pd.DataFrame:
    # Membandingkan berkas raw/ dengan _asli/ sel per sel (urutan baris dipertahankan)
    rows = []
    for f_asli in sorted(asli_dir.glob("*.csv")):
        f_raw = raw_dir / f_asli.name
        if not f_raw.is_file():
            rows.append({"berkas": f_asli.name, "kolom": "*", "sel_berbeda": None,
                         "catatan": "tidak ada di raw/"})
            continue
        a = pd.read_csv(f_asli, dtype=str, keep_default_na=False)
        r = pd.read_csv(f_raw, dtype=str, keep_default_na=False)
        if a.shape != r.shape or list(a.columns) != list(r.columns):
            rows.append({"berkas": f_asli.name, "kolom": "*", "sel_berbeda": None,
                         "catatan": f"bentuk berbeda: asli {a.shape} vs raw {r.shape}"})
            continue
        for col in a.columns:
            n = int((a[col] != r[col]).sum())
            if n:
                rows.append({"berkas": f_asli.name, "kolom": col, "sel_berbeda": n, "catatan": ""})
    return pd.DataFrame(rows, columns=["berkas", "kolom", "sel_berbeda", "catatan"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--reference", type=Path, default=Path("data/reference/kab_prov_kepmendagri_2025.csv"))
    ap.add_argument("--alias", type=Path, default=Path("data/reference/kabupaten_alias.csv"))
    ap.add_argument("--corpus", type=Path, default=Path("data/processed/corpus.parquet"))
    ap.add_argument("--filters", type=Path, default=Path("data/processed/filters.parquet"))
    ap.add_argument("--asli-dir", type=Path, default=Path("data/_asli/data-jadesta"))
    # Pembanding raw_vs_asli: versi Antigravity yang dipakai workload v1 (diarsipkan)
    ap.add_argument("--raw-dir", type=Path, default=Path("data/_v1_antigravity/jadesta"))
    ap.add_argument("--out-dir", type=Path, default=Path("data/reports"))
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    mapper = ProvinceMapper(args.reference, args.alias)
    prov_name = mapper.prov_name

    # Hanya kolom yang diperlukan dibaca (teks dan vektor tidak dimuat)
    cols = ["doc_id", "source_type", "entity_id", "source_file", "row_index",
            "kabupaten", "province", "province_source"]
    corpus = pd.read_parquet(args.corpus, columns=cols)
    N = len(corpus)

    # Penurunan provinsi untuk SELURUH dokumen (dipakai untuk dampak filter)
    kab_lists = corpus["kabupaten"].map(as_list)
    derived = [mapper.derive_codes(k) for k in kab_lists]
    corpus["prov_turunan_kode"] = [d[0] for d in derived]
    corpus["status_kabupaten"] = [d[1] for d in derived]

    # Kode provinsi dari kolom v1 (nama -> kode lewat referensi + alias)
    v1_lists = corpus["province"].map(as_list)
    corpus["prov_v1_kode"] = [sorted({mapper.province_code(p) for p in pl if mapper.province_code(p)})
                              for pl in v1_lists]
    corpus["prov_v1_tidak_dikenal"] = [[p for p in pl if not mapper.province_code(p)] for pl in v1_lists]

    # Laporan per baris JADESTA (semua baris, bukan hanya yang berubah)
    is_jad = corpus["source_type"].astype(str).str.startswith("jadesta")
    jad = corpus[is_jad].copy()
    jad["jenis_selisih"] = [
        jenis_selisih(set(v), u, set(d))
        for v, u, d in zip(jad["prov_v1_kode"], jad["prov_v1_tidak_dikenal"], jad["prov_turunan_kode"])
    ]
    out_rows = pd.DataFrame({
        "source_file": jad["source_file"],
        "row_index": jad["row_index"],
        "entity_id": jad["entity_id"],
        "doc_id": jad["doc_id"],
        "kabupaten": jad["kabupaten"].map(lambda v: "; ".join(as_list(v))),
        "province_v1": jad["province"].map(lambda v: "; ".join(as_list(v))),
        "province_v1_kode": jad["prov_v1_kode"].map("; ".join),
        "province_turunan_kode": jad["prov_turunan_kode"].map("; ".join),
        "province_turunan": jad["prov_turunan_kode"].map(lambda ks: "; ".join(prov_name[k] for k in ks)),
        "status_kabupaten": jad["status_kabupaten"].map("; ".join),
        "jenis_selisih": jad["jenis_selisih"],
    }).sort_values(["source_file", "row_index"])
    out_rows.to_csv(args.out_dir / "province_derivation_jadesta.csv", index=False)

    # Nama kabupaten yang tidak terpetakan (semua sumber), untuk ditinjau manual
    unm = Counter()
    unm_src = {}
    for kl, st, stype in zip(kab_lists, corpus["status_kabupaten"], corpus["source_type"]):
        for k, s in zip(kl, st):
            if s in (ST_TIDAK_DIKENAL, ST_AMBIGU):
                unm[(k, s)] += 1
                unm_src.setdefault((k, s), set()).add(str(stype))
    pd.DataFrame(
        [{"kabupaten": k, "status": s, "jumlah_dokumen": n,
          "source_type": "; ".join(sorted(unm_src[(k, s)]))} for (k, s), n in unm.most_common()],
        columns=["kabupaten", "status", "jumlah_dokumen", "source_type"],
    ).to_csv(args.out_dir / "province_unmapped_kabupaten.csv", index=False)

    # Dampak terhadap filter beku v1 yang memuat predikat provinsi
    filters = pd.read_parquet(args.filters)
    der_sets = corpus["prov_turunan_kode"].map(set)
    v1_sets = corpus["prov_v1_kode"].map(set)
    impact = []
    for f in filters.itertuples():
        spec = f.spec if isinstance(f.spec, dict) else json.loads(f.spec)
        prov_keys = [k for k in spec if "prov" in k.lower()]
        if not prov_keys:
            continue
        val = spec[prov_keys[0]]
        kode = mapper.province_code(val)
        row = {"filter_id": f.filter_id, "type": f.type, "bin": f.bin,
               "province_value": val, "kode_prov": kode,
               "n_eligible_v1_beku": f.n_eligible, "match_rate_v1_beku": f.match_rate,
               "majemuk": len(spec) > 1}
        if len(spec) == 1 and kode:
            n_v1 = int(v1_sets.map(lambda s: kode in s).sum())
            n_der = int(der_sets.map(lambda s: kode in s).sum())
            row.update({"n_eligible_v1_hitung_ulang": n_v1, "n_eligible_turunan": n_der,
                        "match_rate_turunan": n_der / N, "berubah": n_der != f.n_eligible,
                        "catatan": ""})
        else:
            row.update({"n_eligible_v1_hitung_ulang": None, "n_eligible_turunan": None,
                        "match_rate_turunan": None, "berubah": None,
                        "catatan": "predikat majemuk: hitung ulang lewat pipeline filter"
                        if len(spec) > 1 else "nama provinsi tidak dikenal"})
        impact.append(row)
    impact_df = pd.DataFrame(impact)
    impact_df.to_csv(args.out_dir / "province_filter_impact.csv", index=False)

    # Pemeriksaan apakah berkas raw/ sudah dimodifikasi dibanding _asli/
    diff_df = raw_vs_asli(args.asli_dir, args.raw_dir)
    diff_df.to_csv(args.out_dir / "raw_vs_asli_column_diff.csv", index=False)

    # Ringkasan
    st_all = Counter(s for sts in corpus["status_kabupaten"] for s in sts)
    summary = {
        "referensi": str(args.reference),
        "alias_dipakai": bool(mapper.alias_map),
        "n_dokumen": N,
        "n_baris_jadesta": int(is_jad.sum()),
        "jenis_selisih_jadesta": dict(Counter(jad["jenis_selisih"])),
        "status_kabupaten_semua_dokumen": dict(st_all),
        "n_nama_kabupaten_tak_terpetakan": len(unm),
        "filter_provinsi_total": len(impact_df),
        "filter_provinsi_tunggal_berubah": int(impact_df["berubah"].eq(True).sum())
        if len(impact_df) else 0,
        "filter_provinsi_majemuk": int(impact_df["majemuk"].sum()) if len(impact_df) else 0,
        "tipe_filter_di_v1": dict(Counter(filters["type"])),
        "raw_vs_asli_kolom_berbeda": diff_df.groupby("kolom")["sel_berbeda"].sum().to_dict()
        if len(diff_df) else {},
    }
    (args.out_dir / "province_derivation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
