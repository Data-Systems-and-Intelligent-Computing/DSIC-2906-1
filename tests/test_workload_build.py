import numpy as np
import pandas as pd

from src.groundtruth.exact_filtered_knn import exact_filtered_knn
from src.workload.build_filters import filter_mask, spec_id
from src.workload.build_queries import excluded_rows
from src.workload.stratify_match_rate import assign_bin


# Korpus mainan dengan kolom daftar (kabupaten, kategori) dan kolom skalar (sumber, tanggal)
def _korpus():
    return pd.DataFrame({
        "kabupaten": [["Kab A"], ["Kab A", "Kab B"], ["Kab B"], ["Kab C"]],
        "category": [["alam"], ["budaya"], ["alam"], ["desa"]],
        "source_type": ["jadesta_atraksi", "news", "news", "jadesta_desa"],
        "published_at": pd.to_datetime([None, "2026-02-01", "2025-05-01", None]),
    })


def test_filter_mask_list_membership_counts_ambiguous_news():
    # Berita baris 1 tertaut ke Kab A dan Kab B, sehingga cocok untuk keduanya (any_match)
    assert filter_mask(_korpus(), {"kabupaten": "Kab B"}).tolist() == [False, True, True, False]


def test_filter_mask_temporal_excludes_missing_dates():
    assert filter_mask(_korpus(), {"published_at_gte": "2026-01-01"}).tolist() == [False, True, False, False]


def test_filter_mask_compound_is_conjunction():
    spec = {"kabupaten": "Kab B", "source_type": "news", "category": "alam"}
    assert filter_mask(_korpus(), spec).tolist() == [False, False, True, False]


def test_spec_id_is_order_independent():
    assert spec_id({"a": 1, "b": 2}) == spec_id({"b": 2, "a": 1})


def test_assign_bin_lower_bound_inclusive():
    batas = [0, 0.1, 0.5, 2.5, 10, 100]
    label = ["B1", "B2", "B3", "B4", "B5"]
    assert assign_bin([0.05, 0.1, 0.5, 2.49, 10, 40], batas, label).tolist() == ["B1", "B2", "B3", "B3", "B5", "B5"]


def test_excluded_rows_covers_query_duplicates_and_lineage():
    dup_group = np.array([0, 1, 1, 2, 3])          # baris 1 dan 2 bervektor identik
    lineage = np.array(["", "s1", "", "s1", ""])    # baris 1 dan 3 satu story_lineage
    assert excluded_rows(1, dup_group, lineage).tolist() == [1, 2, 3]
    assert excluded_rows(4, dup_group, lineage).tolist() == [4]


def test_exact_groundtruth_breaks_ties_by_row_index():
    base = np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 0.0]])
    q = np.array([1.0, 0.0])
    ids = exact_filtered_knn(base, q, np.array([True, True, True, True]), k=3)
    assert ids.tolist() == [0, 1, 3]
