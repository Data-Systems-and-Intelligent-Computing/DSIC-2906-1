# K-03: Akuisisi Wikipedia dan Wikidata

Status: diputuskan. Supervisor 1 menyatakan Wikipedia dan Wikidata tidak perlu diakuisisi ([tanggal], lewat [chat/bimbingan]).

## Keputusan
Penelitian dijalankan tanpa Wikipedia (D2) dan Wikidata (D4). Korpus terdiri atas tiga
nilai source_type: jadesta_atraksi, jadesta_desa, dan news.

## Dasar
- Arahan Supervisor 1.
- Protokol bagian 14: penelitian dapat dijalankan dengan tiga nilai source_type, dengan
  syarat keterbatasannya dinyatakan.
- Kontribusi penelitian terletak pada evaluasi metode pencarian berfilter, bukan pada
  akuisisi data.
- Workload v2, ground truth gt-v2, embedding, dan indeks sudah dibekukan. Menambah sumber
  sekarang berarti membangun ulang korpus, embedding, indeks, workload, dan ground truth,
  serta mengulang dev benchmark.

## Dampak dan keterbatasan
- Komposisi korpus kurang heterogen dibandingkan rancangan awal.
- Predikat source_type hanya memiliki tiga nilai, sehingga variasi predikat tipe sumber terbatas.
- Teks ensiklopedik yang lebih panjang tidak terwakili; asimetri teks yang ada hanya antara
  JADESTA (templat) dan berita (judul).

## Dinyatakan di
- paper/manuscript.md, bagian 6.1 (Domain specificity).