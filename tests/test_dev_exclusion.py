"""Dev benchmark memakai aturan self-match yang sama dengan workload beku (butir 3)."""
import numpy as np

from src.benchmark.dev_benchmark import eligible_for_query
from src.workload.build_queries import excluded_rows


# Kueri qi=0: baris 1 vektor identik, baris 2 satu story_lineage, baris 3 bebas
def _contoh():
    mask = np.array([True, True, True, True, False])
    dup_group = np.array([7, 7, 1, 2, 3])
    lineage = np.array(["s1", "", "s1", "s2", ""])
    return mask, dup_group, lineage


def test_mengeluarkan_kueri_vektor_identik_dan_lineage():
    mask, dup, lin = _contoh()
    eligible, n_ex = eligible_for_query(mask, 0, dup, lin)
    assert eligible.tolist() == [False, False, False, True, False]
    assert n_ex == 3


def test_sama_dengan_excluded_rows_workload():
    mask, dup, lin = _contoh()
    for qi in range(len(mask)):
        eligible, _ = eligible_for_query(mask, qi, dup, lin)
        harapan = mask.copy()
        harapan[excluded_rows(qi, dup, lin)] = False
        assert np.array_equal(eligible, harapan)


def test_mask_asli_tidak_berubah():
    mask, dup, lin = _contoh()
    salinan = mask.copy()
    eligible_for_query(mask, 0, dup, lin)
    assert np.array_equal(mask, salinan)
