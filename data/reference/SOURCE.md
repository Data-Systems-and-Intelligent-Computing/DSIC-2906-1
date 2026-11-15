# Tabel referensi kabupaten/kota -> provinsi

Berkas: kab_prov_kepmendagri_2025.csv (dibuat oleh scripts/build_reference_kabprov.py)

## Dasar hukum
- Kepmendagri No. 300.2.2-2138 Tahun 2025 tentang Pemberian dan Pemutakhiran Kode,
  Data Wilayah Administrasi Pemerintahan, dan Pulau (ditetapkan 25 April 2025).
- Diubah dengan Kepmendagri No. 300.2.2-2430 Tahun 2025 (ditetapkan 23 Juni 2025);
  perubahan hanya menyangkut data pulau Aceh dan Sumatera Utara, sehingga pemetaan
  kabupaten/kota -> provinsi tidak berubah.

## Berkas sumber 
| Berkas | SHA-256 | Sumber (unduhan) | Halaman katalog | Tanggal unduh |
|---|---|---|---|---|
| Lampiran-Kepmen 300.2.2-2138 Tahun 2025.pdf (lampiran, 4.413 hlm) | ac13b5a57358fcec0503429bb06b2d6b4e5572f65fd0162979b87a79863b1de6 | https://peraturan.bpk.go.id/Download/384753/Lampiran-Kepmen%20300.2.2-2138%20Tahun%202025.pdf | https://peraturan.bpk.go.id/Details/322942/keputusan-mendagri-no-nomor-30022-2138-tahun | 2026-10-29 |
| Kepmen 300.2.2-2138 Tahun 2025.pdf (batang tubuh, 15 hlm) | f403c4b2159054e4556624d8f3724a27ea2ac2281916d21768d3d776434f2c56 | https://peraturan.bpk.go.id/Download/384752/Kepmen%20300.2.2-2138%20Tahun%202025.pdf | https://peraturan.bpk.go.id/Details/322942/keputusan-mendagri-no-nomor-30022-2138-tahun | 2026-10-29 |
| Kepmen_Perubahan_300.2.2-2430.pdf (perubahan, 23 hlm) | 3ef2790683ccddd8bde7b048c6fcef72e10b9189eaf7104c1d55188f51ebc5ab | https://ditjenbinaadwil.kemendagri.go.id/download/file/Kepmen_Perubahan_300.2.2-2430.pdf | https://ditjenbinaadwil.kemendagri.go.id/peraturan/keputusan-menteri-dalam-negeri-300.2.2-2430-2025-228 | 2026-10-29 |

Sumber resmi: JDIH BPK RI (peraturan.bpk.go.id) dan Ditjen Bina Administrasi Kewilayahan
Kemendagri. URL dan tanggal unduh diambil dari metadata berkas macOS (kMDItemWhereFroms,
kMDItemDateAdded).

## Ekstraksi dan validasi
- Teks diambil dengan pdftotext -layout dari lampiran bagian B (rincian kab/kota per provinsi).
- Divalidasi terhadap rekap bagian A: 38 provinsi, 416 kabupaten, 98 kota; jumlah per
  provinsi cocok. Rincian di kab_prov_kepmendagri_2025.meta.json.
- Pembakuan: dua nama ditulis "Kab" pada dokumen resmi dan dibakukan menjadi "Kabupaten"
  (53.02 Timor Tengah Selatan, 95.02 Pegunungan Bintang). Nama asli disimpan di kolom nama_asli.
- Nama provinsi mengikuti dokumen sumber, termasuk 31 = "Daerah Khusus Ibukota Jakarta".
  Predikat provinsi memakai kode_prov, bukan nama.