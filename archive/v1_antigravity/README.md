# Skrip perapian provinsi v1 (Antigravity) - arsip provenance

Skrip di folder ini disalin apa adanya dari folder kerja alat AI Antigravity
(~/.gemini/antigravity/brain/45162689-0933-443f-9745-a2ace0557ff8/). Skrip ini
dipakai untuk workload v1 dan TIDAK dipakai lagi sejak v2 (lihat docs/provinsi-k01.md).

| Berkas | Waktu (WIB) | SHA-256 | Fungsi |
|---|---|---|---|
| scratch_map.json | 9 Okt 2026 22.47 | 0251bff18bc8e17f... | Peta kabupaten -> provinsi yang diunduh Antigravity; sumber dan versinya tidak dicatat |
| add_prov.py | 9 Okt 2026 22.48 | 9d4a763806e1dffb... | Mengisi kolom provinsi berkas JADESTA (wisata_*.csv, desa_wisata_*.csv) |
| add_prov2.py | 9 Okt 2026 22.59 | 96e801c660ebfd85... | Mengisi kolom Provinsi berkas berita (hasil_scraping_pertama_jadesta ... Berita *.csv) |

Catatan isi skrip:
- Nama provinsi diubah dengan title(); dari sinilah "DK Jakarta" menjadi "DKI Jakarta".
- Wilayah Papua dipecah manual ke provinsi pemekaran 2022 (daftar PAPUA).
- Daftar EXTRA menetapkan provinsi secara manual untuk nilai kabupaten yang rusak
  ("inferred from desa/alamat"), termasuk kabupaten kosong -> "Sulawesi Utara"
  (contoh wisata_alam.csv:5519). Pengisian ini adalah tebakan dan melanggar K-01.
- Skrip dijalankan dengan argumen "apply" di folder data dan menimpa berkas di tempat.
