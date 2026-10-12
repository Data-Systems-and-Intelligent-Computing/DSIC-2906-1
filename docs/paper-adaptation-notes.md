# Paper adaptation notes

Do not copy production thresholds blindly. The reference paper uses a much larger corpus; DSIC-2906 must audit empirical match-rate distributions and choose feasible `n_sample` values for its own index size.

Implementation fidelity checklist:
- same similarity metric across exact and approximate search;
- predicate-agnostic shared graph;
- verified TwoHop traversal;
- verified AdaptiveL frontier expansion and Algorithm-3 scaling;
- log all deviations from the anchor implementation;
- keep original AdaptiveL results even if RC-AdaptiveL is evaluated.

## Implementation log (DSIC-2906-1, 13 Oktober 2026)

Sumber: Liu et al. (2026), *Metadata-Filtered Vector Search in the WebIQ Grounding Index* (PDF 6 halaman, Algorithm 1–3). Implementasi B1 dan P1 sudah dicocokkan dengan pseudocode tersebut.

### Kesesuaian dengan paper

| Komponen | Paper | Implementasi DSIC-2906-1 | Status |
|---|---|---|---|
| Graf | DiskANN, R = 64, L = 100 (eksperimen publik) | `diskannpy` 0.7.0, R = 64, L_build = 100, cosine | Sama |
| B1 TwoHop (Algorithm 1) | Frontier = titik awal + titik lolos predikat; tetangga gagal dikumpulkan di U; dua-hop dari U bila \|U\| > \|N_out(p*)\|/2; frontier dipangkas ke L_search | `src/search/twohop.py` | Sama |
| P1 AdaptiveL (Algorithm 2) | Navigasi tanpa memedulikan predikat; predikat dievaluasi pada titik yang dikunjungi; hasil = titik dikunjungi yang lolos; pada \|V\| = n_sample, L_search diskalakan | `src/search/adaptivel.py` | Sama |
| Algorithm 3 | 0 → m_max; ≥ 0,5 → 1; ≥ 0,1 → 2; selainnya min(m_max, 2^(−log10 sp)) | `compute_adaptive_multiplier` | Sama |

### Deviasi dan interpretasi

1. **Baris 10 Algorithm 2 pada paper tertulis `L_search ← L_search`** (faktor pengali tidak tercetak). Diinterpretasikan sebagai `L_search ← L_search × ComputeAdaptiveL(n_match / n_sample, m)`, sesuai teks bagian 2 ("expand the frontier by 2^log n") dan Algorithm 3.
2. **Traversal ditulis ulang di Python** karena `diskannpy` hanya membuka `search`/`batch_search`. Penelusuran tanpa filter identik dengan `diskannpy` (top-10 sama pada 200 kueri uji). QPS/latency tidak sebanding dengan C++ DiskANN maupun dengan angka paper; hanya perbandingan antarmetode yang sah.
3. **Frontier memakai dua heap** (`Beam` di `src/search/graph_index.py`); terbukti identik dengan daftar terurut yang dipangkas (0 perbedaan pada 540 perbandingan), 8,5× lebih cepat. Titik yang tersingkir dari frontier tidak kembali masuk (praktik DiskANN); pseudocode paper menulis `N_out(p*) \ V`, yang secara harfiah dapat memasukkan kembali titik yang pernah dipangkas.
4. **n_sample disesuaikan ukuran korpus.** Di paper (produksi) 1000; di DSIC-2906-1 jumlah titik yang dikunjungi ≈ L_search (±100 pada L = 100), sehingga n_sample harus < L. Grid dev: 32 dan 64.
5. **β-search tidak diimplementasikan** (paper menundanya ke future work).
6. **Biaya predikat**: di korpus ini predikat adalah mask boolean (sangat murah); di paper evaluasi predikat dianggap jauh lebih murah dari perhitungan jarak, tetapi tidak gratis.

### Catatan cakupan rezim

Paper menunjukkan TwoHop runtuh pada match rate 0,01–0,1% (YFCC, Gambar 1a). Dengan syarat kecukupan protokol (≥ 10 × k = 100 titik, setara ≥ 0,155%), rezim < 0,155% tidak pernah diuji, sehingga keunggulan AdaptiveL yang dilaporkan paper berada di luar jangkauan workload saat ini.
