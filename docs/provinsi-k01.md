# Provinsi JADESTA: provenance perapian v1 dan penurunan ulang (K-01 / DL-10)

Status: workload v1 dan gt-v1 digantikan oleh workload v2 dan gt-v2 (commit 34b187e).

## 1. Perapian kolom provinsi pada v1 (provenance)

- Pelaksana: Feby Angelina, dibantu alat AI Antigravity.
- Waktu: 13 Oktober 2026, sekitar 01.03 WIB (waktu modifikasi berkas di data/raw/jadesta/), sebelum build_corpus.py v1.
- Permintaan ke Antigravity: menyesuaikan kabupaten/kota untuk mengisi kolom provinsi.
- Tabel pemetaan yang dipakai Antigravity tidak dicatat dan tidak berasal dari sumber resmi
  berversi. Hasilnya ditulis langsung menimpa berkas di data/raw/jadesta/, sehingga berkas
  "raw" pada v1 bukan berkas asli (bertentangan dengan Protokol bagian 16 langkah 1).
- Cakupan perubahan: hanya kolom provinsi, 16.340 sel
  (wisata_alam 6.569, wisata_buatan 3.094, wisata_budaya 5.469, desa_wisata_berkembang 405,
  desa_wisata_maju 193, desa_wisata_mandiri 16, desa_wisata_rintisan 594).
  Kolom lain tidak berubah (data/reports/raw_vs_asli_column_diff.csv).
- Temuan: 52 baris JADESTA yang kabupatennya kosong atau berisi teks lain akibat kolom bergeser
  saat scraping (contoh: "Saribattang", "Sendangmulyo", "berwawasan") tetap diberi provinsi.
  Contoh: wisata_alam.csv:5519, kabupaten kosong, provinsi diisi "Sulawesi Utara".
  Pengisian ini tidak dapat diturunkan dari kabupaten, sehingga melanggar K-01.
- Label di manifest v1 ("pengumpul data", lalu "peneliti (dibantu Antigravity)") diganti
  dengan catatan ini.

## 2. Penurunan ulang sesuai K-01

- Tabel referensi: Lampiran Kepmendagri 300.2.2-2138/2025 sebagaimana diubah 300.2.2-2430/2025
  (data/reference/, sumber dan SHA-256 di SOURCE.md); 38 provinsi, 416 kabupaten, 98 kota,
  divalidasi terhadap rekap resmi (commit 198dc41).
- Alias: 18 variasi ejaan dengan padanan resmi tunggal, masing-masing dengan alasan
  (data/reference/kabupaten_alias.csv), contoh "Kota B A T A M" -> Kota Batam.
- Nama yang bukan kabupaten (10 nilai) dan kabupaten kosong tidak diberi provinsi.
- Aturan dipakai bersama oleh build corpus dan laporan (src/corpus/province_map.py).
- Berkas data/raw/jadesta/ dikembalikan ke berkas asli (SHA-256 identik dengan data/_asli/);
  versi Antigravity diarsipkan di data/_v1_antigravity/ (di-ignore, diunggah ke bucket).
  Hash ketiga versi: data/manifests/jadesta_sha256.csv.

## 3. Laporan selisih v1 terhadap turunan (semua baris JADESTA)

- 21.461 baris JADESTA: 21.409 sama, 52 v1 terisi tetapi turunan kosong, 0 beda provinsi
  (data/reports/province_derivation_jadesta.csv).
- Di seluruh korpus: 64.086 dokumen terpetakan penuh, 94 sebagian, 174 tak terpetakan.

## 4. Dampak terhadap workload

| | v1 | v2 |
|---|---|---|
| Pasangan kueri-filter | 2.034 | 2.040 |
| Kueri unik | 1.987 | 2.008 |
| Pasangan per bin | B1 291, B2 663, B3 360, B4 420, B5 300 | B1 297, B2 663, B3 360, B4 420, B5 300 |
| checksum workload.parquet | 3b230b33... | b5d7d6f8... |

- doc_id dan teks korpus identik dengan v1; embedding dan indeks tetap berlaku.
- 24 filter berubah n_eligible (9 provinsi, 15 provinsi_tipe_sumber); tidak ada yang pindah bin
  atau berubah status kelayakan. 8 filter berganti nama karena memakai nama provinsi resmi
  (DI Yogyakarta -> Daerah Istimewa Yogyakarta; DKI Jakarta -> Daerah Khusus Ibukota Jakarta).
- Hanya 640 pasangan identik dengan v1: sampling memakai RNG berurutan per sel, sehingga
  perubahan pada sel provinsi menggeser sampel sel-sel berikutnya. Seed (2906), konfigurasi,
  batas bin, ambang kecukupan, dan ambang sindikasi tidak diubah. v1 belum dipakai untuk E2.

## 5. Usulan entri decision log

DL-(menunggu nomor dari pembimbing) (29 Okt 2026) Workload v2.
Workload v1 dan gt-v1 tidak dipakai karena provinsi v1 berasal dari perapian berbantuan AI
tanpa tabel pemetaan berversi. Provinsi diturunkan dari kabupaten lewat tabel Kepmendagri
300.2.2-2138/2025 (+18 alias yang ditinjau); kabupaten kosong/tidak dikenal ditandai tak
terpetakan. Workload dan ground truth dibekukan ulang sebagai v2 (commit 34b187e) dengan seed,
konfigurasi, dan batas bin yang sama. Arsip v1 disimpan beserta SHA-256.
