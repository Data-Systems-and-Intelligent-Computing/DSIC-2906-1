"""Membangun tabel referensi kabupaten/kota -> provinsi dari Lampiran
Kepmendagri No. 300.2.2-2138 Tahun 2025 (K-01 / DL-10).

Builds the kabupaten/kota -> province reference table from the official
Kepmendagri 300.2.2-2138/2025 annex PDF, and validates it against the
annex's own recap table (section A).

Sumber:
- Bagian A lampiran: rekap per provinsi (kode, nama, jumlah kab, jumlah kota).
- Bagian B lampiran: rincian kode kabupaten/kota, muncul satu kali per provinsi
  (38 kali), selalu diikuti bagian C (kecamatan).
- Kepmendagri 300.2.2-2430/2025 hanya mengubah data pulau Aceh dan Sumatera
  Utara, sehingga pemetaan kab/kota -> provinsi dari 2138 tidak berubah.

Keluaran (di --out-dir):
- kab_prov_kepmendagri_2025.csv : satu baris per kabupaten/kota
- kab_prov_kepmendagri_2025.meta.json : SHA-256 PDF, versi pdftotext, hasil validasi

Pemakaian:
    python scripts/build_reference_kabprov.py \
        --pdf /path/Lampiran-Kepmen_300_2_2-2138_Tahun_2025.pdf \
        --out-dir data/reference

Membutuhkan pdftotext (poppler-utils). Skrip keluar dengan kode 1 bila
validasi terhadap rekap bagian A gagal; CSV tetap ditulis untuk diperiksa.
"""

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Rekap resmi seluruh Indonesia menurut bagian A lampiran (dipakai sebagai cek akhir)
EXPECTED_PROVINSI = 38
EXPECTED_KABUPATEN = 416
EXPECTED_KOTA = 98

# Penanda awal bagian A, B, dan C pada teks hasil pdftotext -layout
RE_SECTION_A = re.compile(r"^\s*A\. Rekapitulasi Kode")
RE_SECTION_B = re.compile(r"^\s*B\. Rincian Kode")
RE_SECTION_C = re.compile(r"^\s*C\. Rincian Kode")

# Baris rekap provinsi bagian A: "<no> <kode 2 digit> <nama provinsi> <kab> <kota> ..."
RE_PROV_ROW = re.compile(
    r"^\s*(?P<no>\d{1,2})\s+(?P<kode>\d{2})\s+(?P<nama>[A-Za-z][A-Za-z .'-]*?)\s{2,}"
    r"(?P<kab>\d+)\s+(?P<kota>\d+)\s"
)

# Baris kab/kota bagian B: "<no> <kode NN.NN> <Kabupaten|Kab|Kab.|Kota> <nama>  <kolom berikutnya>"
# Nama berakhir pada jeda >= 2 spasi (batas kolom pada mode -layout)
RE_KABKOTA_ROW = re.compile(
    r"^\s*(?P<no>\d{1,3})\s+(?P<kode>\d{2}\.\d{2})\s+"
    r"(?P<jenis>Kabupaten|Kab\.?|Kota)\s+(?P<nama>\S.*?)(?:\s{2,}|$)"
)


def sha256_file(path: Path) -> str:
    # Hash SHA-256 berkas sumber untuk dicatat di SOURCE.md
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pdftotext_version() -> str:
    # Versi pdftotext ikut dicatat karena hasil ekstraksi bergantung padanya
    out = subprocess.run(["pdftotext", "-v"], capture_output=True, text=True)
    return (out.stderr or out.stdout).splitlines()[0].strip()


def extract_text(pdf: Path) -> list[str]:
    # Ekstraksi teks dengan mempertahankan tata letak kolom
    if not pdf.is_file():
        sys.exit(f"PDF tidak ditemukan: {pdf}")
    out = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"],
        capture_output=True, text=True,
    )
    # pdftotext menulis galat ke stderr; ditampilkan bila proses gagal
    if out.returncode != 0:
        sys.exit(f"pdftotext gagal (kode {out.returncode}): {out.stderr.strip()}")
    return out.stdout.splitlines()


def parse_rekap_provinsi(lines: list[str]) -> dict[str, dict]:
    # Mengambil 38 baris rekap provinsi dari bagian A (sebelum bagian B pertama)
    provinsi = {}
    in_a = False
    for line in lines:
        if RE_SECTION_A.match(line):
            in_a = True
            continue
        if RE_SECTION_B.match(line):
            break
        if not in_a:
            continue
        m = RE_PROV_ROW.match(line)
        if m:
            provinsi[m["kode"]] = {
                "nama_prov": " ".join(m["nama"].split()),
                "jumlah_kab": int(m["kab"]),
                "jumlah_kota": int(m["kota"]),
            }
    return provinsi


def parse_kabkota(lines: list[str]) -> list[dict]:
    # Mengambil baris kab/kota hanya dari rentang bagian B .. bagian C
    rows = []
    in_b = False
    for lineno, line in enumerate(lines, start=1):
        if RE_SECTION_B.match(line):
            in_b = True
            continue
        if RE_SECTION_C.match(line):
            in_b = False
            continue
        if not in_b:
            continue
        m = RE_KABKOTA_ROW.match(line)
        if not m:
            continue
        jenis_asli = m["jenis"]
        nama = " ".join(m["nama"].split())
        # "Kab" / "Kab." pada dokumen resmi dibakukan menjadi "Kabupaten"
        jenis = "Kota" if jenis_asli == "Kota" else "Kabupaten"
        rows.append({
            "kode_kab": m["kode"],
            "nama_kab": f"{jenis} {nama}",
            "jenis": jenis.lower(),
            "nama_asli": f"{jenis_asli} {nama}",
            "dibakukan": int(jenis_asli not in ("Kabupaten", "Kota")),
            "baris_teks": lineno,
        })
    return rows


def validate(provinsi: dict, rows: list[dict]) -> list[str]:
    # Mencocokkan hasil ekstraksi bagian B dengan rekap bagian A
    errors = []

    if len(provinsi) != EXPECTED_PROVINSI:
        errors.append(f"jumlah provinsi rekap {len(provinsi)} != {EXPECTED_PROVINSI}")

    # Kode kab/kota harus unik
    dup = [k for k, n in Counter(r["kode_kab"] for r in rows).items() if n > 1]
    if dup:
        errors.append(f"kode kab/kota ganda: {sorted(dup)}")

    # Prefiks kode kab/kota harus merupakan kode provinsi yang ada di rekap
    orphan = sorted({r["kode_kab"] for r in rows if r["kode_kab"][:2] not in provinsi})
    if orphan:
        errors.append(f"kode kab/kota tanpa provinsi di rekap: {orphan}")

    # Jumlah kabupaten dan kota per provinsi harus sama dengan rekap
    per_prov = Counter((r["kode_kab"][:2], r["jenis"]) for r in rows)
    for kode, p in sorted(provinsi.items()):
        n_kab = per_prov[(kode, "kabupaten")]
        n_kota = per_prov[(kode, "kota")]
        if (n_kab, n_kota) != (p["jumlah_kab"], p["jumlah_kota"]):
            errors.append(
                f"{kode} {p['nama_prov']}: terekstrak kab={n_kab} kota={n_kota}, "
                f"rekap kab={p['jumlah_kab']} kota={p['jumlah_kota']}"
            )

    # Total nasional
    n_kab = sum(1 for r in rows if r["jenis"] == "kabupaten")
    n_kota = sum(1 for r in rows if r["jenis"] == "kota")
    if (n_kab, n_kota) != (EXPECTED_KABUPATEN, EXPECTED_KOTA):
        errors.append(
            f"total terekstrak kab={n_kab} kota={n_kota}, "
            f"harapan kab={EXPECTED_KABUPATEN} kota={EXPECTED_KOTA}"
        )
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pdf", required=True, type=Path, help="PDF lampiran Kepmendagri 300.2.2-2138/2025")
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()

    # Ekstraksi dan parsing
    lines = extract_text(args.pdf)
    provinsi = parse_rekap_provinsi(lines)
    rows = parse_kabkota(lines)

    # Melengkapi kode dan nama provinsi untuk setiap kab/kota
    for r in rows:
        kode_prov = r["kode_kab"][:2]
        r["kode_prov"] = kode_prov
        r["nama_prov"] = provinsi.get(kode_prov, {}).get("nama_prov", "")
    rows.sort(key=lambda r: r["kode_kab"])

    errors = validate(provinsi, rows)

    # Penulisan CSV referensi
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = args.out_dir / "kab_prov_kepmendagri_2025.csv"
    fields = ["kode_kab", "nama_kab", "jenis", "kode_prov", "nama_prov", "nama_asli", "dibakukan"]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # Penulisan metadata provenance dan hasil validasi
    meta = {
        "sumber": "Lampiran Kepmendagri No. 300.2.2-2138 Tahun 2025 "
                  "(sebagaimana diubah Kepmendagri No. 300.2.2-2430 Tahun 2025; "
                  "perubahan hanya menyangkut data pulau)",
        "pdf_nama": args.pdf.name,
        "pdf_sha256": sha256_file(args.pdf),
        "pdftotext": pdftotext_version(),
        "dibuat_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "jumlah_provinsi": len(provinsi),
        "jumlah_kabupaten": sum(1 for r in rows if r["jenis"] == "kabupaten"),
        "jumlah_kota": sum(1 for r in rows if r["jenis"] == "kota"),
        "nama_dibakukan": [r["nama_asli"] + " -> " + r["nama_kab"]
                           for r in rows if r["dibakukan"]],
        "validasi_lulus": not errors,
        "validasi_galat": errors,
    }
    out_meta = args.out_dir / "kab_prov_kepmendagri_2025.meta.json"
    out_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # Ringkasan ke layar
    print(f"provinsi={meta['jumlah_provinsi']} kabupaten={meta['jumlah_kabupaten']} "
          f"kota={meta['jumlah_kota']} -> {out_csv}")
    for s in meta["nama_dibakukan"]:
        print(f"  dibakukan: {s}")
    if errors:
        print("VALIDASI GAGAL:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("validasi terhadap rekap bagian A: lulus")
    return 0


if __name__ == "__main__":
    sys.exit(main())
