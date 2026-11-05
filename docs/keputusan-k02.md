# K-02: Asimetri panjang teks antar-sumber

Status: usulan, mengikuti rekomendasi Supervisor 2 (protokol bagian 13, alternatif B);
menunggu konfirmasi Supervisor 1 (bimbingan 6 November 2026).

## Keputusan yang diusulkan
Alternatif B: source_type tetap dipakai sebagai predikat, dengan pelaporan yang jujur.

## Yang sudah dilaksanakan
- source_type dipertahankan dalam predikat (tipe_sumber dan provinsi_tipe_sumber).
- Statistik panjang teks per source_type dilaporkan
  (data/processed/text_length_by_source.csv): median 133 karakter (atraksi), 152 (desa),
  74 (berita).
- Asimetri dan efek templat teks JADESTA dinyatakan sebagai ancaman validitas
  (paper/manuscript.md bagian 6.1, Embedding bias and text asymmetry).
- Hasil utama dipecah per sumber kueri dan per query_in_filter (src/evaluation/report.py).
  Dev benchmark menunjukkan perbedaan recall antar-sumber yang besar pada predikat khusus
  berita (contoh PostFilter 3200, penerbit=jawapos.com: kueri berita 1,000, atraksi 0,246,
  desa 0,030), sehingga interpretasinya dibatasi dan tidak diatribusikan sepenuhnya kepada
  selektivitas filter.

## Yang tidak dilaksanakan
- Normalisasi panjang dokumen (misalnya memotong teks JADESTA agar sepanjang judul berita)
  tidak dilakukan. Teks setiap sumber dibentuk sesuai protokol bagian 16 langkah 6, dan
  embedding, indeks, workload, serta ground truth sudah dibekukan dari teks tersebut.
  Bila normalisasi diwajibkan, seluruh tahap tersebut harus dibangun ulang.

## Pilihan untuk Supervisor 1
1. Pelaporan seperti di atas sudah cukup (alternatif B tanpa normalisasi).
2. Ditambah analisis sensitivitas: varian teks pendek (nama + kategori untuk JADESTA)
   dengan embedding dan indeks tambahan, hasil utama tetap beku.
3. Normalisasi penuh: korpus, embedding, indeks, workload, dan ground truth dibangun ulang (v3).