"""Pemetaan kabupaten/kota -> provinsi dari tabel referensi resmi (K-01 / DL-10).

Dipakai oleh src.corpus.build_corpus (kolom province di korpus) dan
scripts/province_derive.py (laporan selisih terhadap workload v1), sehingga
keduanya memakai aturan yang sama persis.

Aturan:
- Provinsi hanya diisi bila nama kabupaten/kota cocok dengan tabel referensi
  Kepmendagri 300.2.2-2138/2025, atau dengan alias yang sudah ditinjau manual
  (data/reference/kabupaten_alias.csv).
- Kabupaten kosong atau nama yang tidak dikenal tidak diberi provinsi (tidak ditebak).
- Nama provinsi yang dihasilkan adalah nama resmi dari tabel referensi.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REFERENCE_CSV = Path("data/reference/kab_prov_kepmendagri_2025.csv")
ALIAS_CSV = Path("data/reference/kabupaten_alias.csv")

# Variasi nama provinsi yang mungkin muncul di kolom provinsi lama, dipetakan ke kode resmi
PROV_ALIAS = {
    "dki jakarta": "31",
    "dk jakarta": "31",
    "daerah khusus jakarta": "31",
    "daerah khusus ibukota jakarta": "31",
    "daerah khusus ibu kota jakarta": "31",
    "jakarta": "31",
    "di yogyakarta": "34",
    "diy": "34",
    "yogyakarta": "34",
    "daerah istimewa yogyakarta": "34",
    "nanggroe aceh darussalam": "11",
    "bangka belitung": "19",
    "kep bangka belitung": "19",
    "kep riau": "21",
}

# Status pemetaan satu nama kabupaten
ST_OK = "terpetakan"
ST_ALIAS = "terpetakan_alias"
ST_KOSONG = "tak_terpetakan_kabupaten_kosong"
ST_TIDAK_DIKENAL = "tak_terpetakan_nama_tidak_dikenal"
ST_AMBIGU = "ambigu"

# Nilai province_source per dokumen di korpus
SRC_TURUNAN = "turunan_kab_kepmendagri_2025"
SRC_SEBAGIAN = "turunan_kab_kepmendagri_2025_sebagian"
SRC_TAK_TERPETAKAN = "tak_terpetakan"


def norm_kab(s: str) -> str:
    # Normalisasi nama kab/kota untuk kunci join; jenis Kabupaten/Kota tetap dibedakan
    s = str(s).lower().strip()
    s = re.sub(r"\bkab\.?(?=\s)", "kabupaten", s)
    s = re.sub(r"\bkep\.?(?=\s)", "kepulauan", s)
    s = re.sub(r"\badministrasi\b", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(s.split())


def norm_prov(s: str) -> str:
    # Normalisasi nama provinsi untuk dipetakan ke kode
    s = str(s).lower().strip()
    s = re.sub(r"\bprov(insi)?\.?\s+", "", s)
    s = re.sub(r"\bkep\.?(?=\s)", "kep", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(s.split())


def as_list(v) -> list[str]:
    # Kolom list di parquet bisa berupa ndarray, list, string, atau kosong
    if v is None:
        return []
    if isinstance(v, (list, tuple, np.ndarray)):
        return [str(x) for x in v if x is not None and str(x).strip() and str(x) != "nan"]
    if isinstance(v, float) and np.isnan(v):
        return []
    s = str(v).strip()
    return [s] if s and s != "nan" else []


class ProvinceMapper:
    """Memuat tabel referensi + alias dan memetakan nama kabupaten ke provinsi."""

    def __init__(self, reference_csv: Path = REFERENCE_CSV, alias_csv: Path | None = ALIAS_CSV):
        ref = pd.read_csv(reference_csv, dtype=str)

        # Nama kabupaten ternormalisasi -> himpunan (kode_kab, kode_prov)
        self.kab_map: dict[str, set] = {}
        for r in ref.itertuples():
            self.kab_map.setdefault(norm_kab(r.nama_kab), set()).add((r.kode_kab, r.kode_prov))
        self.prov_name: dict[str, str] = dict(zip(ref["kode_prov"], ref["nama_prov"]))

        # Nama provinsi (resmi + alias) -> kode
        self.prov_map = {norm_prov(n): k for k, n in self.prov_name.items()}
        self.prov_map.update({norm_prov(a): k for a, k in PROV_ALIAS.items()})

        # Alias kabupaten hasil tinjauan manual
        self.alias_map: dict[str, tuple[str, str]] = {}
        if alias_csv and Path(alias_csv).is_file():
            al = pd.read_csv(alias_csv, dtype=str)
            kode_to_prov = dict(zip(ref["kode_kab"], ref["kode_prov"]))
            for r in al.itertuples():
                if r.kode_kab not in kode_to_prov:
                    sys.exit(f"alias {r.nama_jadesta!r}: kode_kab {r.kode_kab} tidak ada di referensi")
                self.alias_map[norm_kab(r.nama_jadesta)] = (r.kode_kab, kode_to_prov[r.kode_kab])

    def map_kabupaten(self, name: str) -> tuple[str, str | None, str | None]:
        # Memetakan satu nama kabupaten; mengembalikan (status, kode_kab, kode_prov)
        key = norm_kab(name)
        if not key:
            return ST_KOSONG, None, None
        hits = self.kab_map.get(key)
        if hits and len(hits) == 1:
            kode_kab, kode_prov = next(iter(hits))
            return ST_OK, kode_kab, kode_prov
        if hits and len(hits) > 1:
            return ST_AMBIGU, None, None
        if key in self.alias_map:
            kode_kab, kode_prov = self.alias_map[key]
            return ST_ALIAS, kode_kab, kode_prov
        return ST_TIDAK_DIKENAL, None, None

    def derive_codes(self, kab_list: list[str]) -> tuple[list[str], list[str]]:
        # Kode provinsi turunan untuk satu dokumen (bisa lebih dari satu kabupaten)
        if not kab_list:
            return [], [ST_KOSONG]
        provs, statuses = [], []
        for k in kab_list:
            st, _, kp = self.map_kabupaten(k)
            statuses.append(st)
            if kp and kp not in provs:
                provs.append(kp)
        return sorted(provs), statuses

    def province_code(self, name: str) -> str | None:
        # Kode provinsi untuk sebuah nama provinsi (resmi atau alias)
        return self.prov_map.get(norm_prov(name))

    def derive_column(self, kabupaten: pd.Series) -> tuple[list[list[str]], list[str]]:
        # Kolom province (nama resmi) dan province_source untuk seluruh korpus
        provinces, sources = [], []
        for v in kabupaten:
            codes, statuses = self.derive_codes(as_list(v))
            provinces.append([self.prov_name[c] for c in codes])
            mapped = [s in (ST_OK, ST_ALIAS) for s in statuses]
            if all(mapped):
                sources.append(SRC_TURUNAN)
            elif any(mapped):
                sources.append(SRC_SEBAGIAN)
            else:
                sources.append(SRC_TAK_TERPETAKAN)
        return provinces, sources
