# Failure taxonomy

Minimum categories:
- under-filled top-k after filtering;
- low filtered recall;
- timeout/resource cap;
- predicate evaluation mismatch;
- missing/incorrect metadata;
- duplicate or syndicated-content dominance;
- query self-match leakage;
- implementation deviation from paper pseudocode;
- unstable repeated-query results.

Audit concrete cases; do not infer cause solely from aggregate metrics.

## Hasil audit benchmark utama (Lightsail, 15 Nov 2026)

Sumber: `results/raw/main_{single,compound}_lightsail-t3.xlarge-thread1_2026-11-15.jsonl` (24.480 baris, commit `ddf690c`),
tabel `results/summary/main_lightsail-t3.xlarge-thread1_2026-11-15_{utama,ekstensi}/failure_taxonomy.csv`.
Angka di bawah memakai konfigurasi terbesar tiap metode (AdaptiveL L=400, PostFilter 3.200, TwoHop L=400), kecuali disebut lain.

| Kategori | Temuan | Bukti |
|---|---|---|
| Timeout / batas sumber daya | Tidak terjadi | 0 dari 24.480 baris; profil 1/2/4 core juga 0 (`resource_2026-11-15.csv`) |
| Pelanggaran predikat | Tidak terjadi | runner menghentikan run bila ada hasil yang tidak lolos filter; run selesai tanpa henti |
| Kebocoran self-match | Tidak terjadi | 0 baris yang memuat `query_row` di `result_rows` |
| Hasil tidak stabil | Tidak terjadi | 100 % pasangan x konfigurasi identik di 5 ulangan (`pct_identik` di ringkasan stabilitas) |
| Dominasi sindikasi | Dapat diabaikan | 0,05 % hasil AdaptiveL/PostFilter dan 0 % TwoHop memuat > 50 % dokumen dari satu `story_lineage_id` |
| Under-filled top-k | Kegagalan utama AdaptiveL dan PostFilter | lihat F-1 dan F-3 |
| Penghentian dini TwoHop | Kegagalan utama TwoHop di set ekstensi | lihat F-2 |
| Recall rendah dengan hasil penuh | Jarang | maks. 6,6 % baris (TwoHop, ekstensi B2); 0–1,9 % pada set utama |
| Penyimpangan implementasi | Tidak ditemukan | uji pseudocode Algorithm 1–3 (`docs/paper-adaptation-notes.md`), 67 tes lulus |
| Metadata | Dicatat, tidak diubah | 9.804 berita berwilayah ambigu memakai any-match (DT-3) |

### F-1. Under-fill bergantung pada hubungan kueri dan filter

Proporsi hasil under-filled menurut `query_in_filter` (kueri termasuk dokumen yang lolos filternya sendiri atau tidak):

| Set | Metode | Kueri di luar filter | Kueri di dalam filter |
|---|---|---|---|
| utama | AdaptiveL | 36,4 % | 8,6 % |
| utama | PostFilter | 34,3 % | 4,2 % |
| utama | TwoHop | 1,2 % | 1,2 % |
| ekstensi | AdaptiveL | 90,9 % | 49,2 % |
| ekstensi | PostFilter | 90,6 % | 40,9 % |
| ekstensi | TwoHop | 52,5 % | 51,5 % |

Bila kueri berada di luar filter, tetangga terdekatnya di graf umumnya tidak lolos filter, sehingga metode yang menelusuri
graf tanpa memedulikan filter (AdaptiveL, PostFilter) kehabisan anggaran sebelum mengumpulkan k dokumen lolos. TwoHop tidak
terpengaruh pada set utama karena hanya menelusuri simpul yang lolos. Ini sesuai Bab 2 subbab 2.5 dan 2.8.3 (bias lokal).

Contoh paling jelas: filter `temporal` di B5 (match rate sekitar 47 %). Untuk kueri di luar filter, recall AdaptiveL 0,43
dan under-fill 63 %, sedangkan kueri di dalam filter recall 1,00. Kueri dari desa wisata JADESTA (tanpa tanggal terbit)
mendapat recall 0,0 dengan under-fill 100 %, karena sekitarnya hanya berisi dokumen JADESTA yang tidak lolos filter tanggal.
Match rate global tinggi tidak menjamin dokumen lolos tersedia di sekitar kueri.

### F-2. TwoHop berhenti terlalu dini pada filter sangat selektif

Pada set ekstensi, 52 % pencarian TwoHop berhenti setelah mengunjungi paling banyak 10 simpul (median 1 simpul pada filter
penerbit dan kabupaten x kategori B1), dan recall tidak berubah ketika L dinaikkan dari 100 ke 400. Frontier TwoHop hanya
berisi simpul lolos; bila tetangga satu dan dua langkah dari titik awal tidak ada yang lolos, frontier habis.
Ini kelemahan pertama TwoHop yang dicatat Liu dkk. (match rate sekitar 0,1 % atau lebih rendah). Pada set utama hanya 1,2 %.

### F-3. Pengali AdaptiveL tersaturasi karena n_sample = 32

Proporsi pencarian AdaptiveL dengan ŝp = 0 (pengali = m_max = 8): B1 77 %, B2 63 %, B3 56 %, B4 36 %, B5 20 %.
Pada B1–B3 jumlah simpul dikunjungi hampir tepat 8 x L, sehingga AdaptiveL berperilaku seperti PostFilter dengan anggaran
L x 8 (DT-4) dan recall-nya sedikit di bawah PostFilter 3.200. Ini sesuai prediksi Bab 2 subbab 2.8.2 (peluang sampel kosong)
dan bukan kesalahan implementasi.

### Kategori yang tidak dapat dinilai dari log

`metadata_incorrect` tidak dapat dideteksi otomatis karena ground truth dibentuk dari metadata yang sama; kebenaran metadata
bergantung pada audit korpus (protokol T-01 s.d. T-04, `docs/provinsi-k01.md`).

### F-4. Timeout ketat memotong perluasan frontier AdaptiveL (DT-7)

Sumber: `results/summary/parallel_2026-11-15/concurrent_stability_t{700,45}_2026-11-15_ringkas.csv` (dua salinan kueri
identik dijalankan bersamaan oleh 4 proses).

- Timeout 700 ms: 0 % timeout dan 100 % hasil identik untuk ketiga metode; eksekusi bersamaan saja tidak menimbulkan ketidakstabilan.
- Timeout 45 ms: timeout terpicu pada AdaptiveL 19-60 %, PostFilter 33-36 %, TwoHop 0-92 % pencarian. Hasil identik antarsalinan
  AdaptiveL 94-99 %, PostFilter 98,5-99,7 %, TwoHop 99,4-100 %. Recall AdaptiveL (L = 400) turun paling banyak
  (utama B2 0,69 -> 0,46; B3 0,85 -> 0,64), PostFilter dan TwoHop hampir tidak berubah.
- Mekanisme: timeout memotong kunjungan tambahan hasil pengali AdaptiveL (sampai 8 x L), sedangkan TwoHop umumnya sudah
  menemukan hasilnya sebelum timeout dan yang terpotong hanya ekor pemeriksaan predikat.
- Batasan: 45 ms diambil dari batas latensi produksi paper (bagian 3.2), tetapi relatif jauh lebih ketat untuk implementasi
  Python ini (median latensi AdaptiveL L = 400 sekitar 40 ms). Hasil ini menggambarkan perilaku pada anggaran waktu ketat,
  bukan replikasi kondisi produksi paper.
