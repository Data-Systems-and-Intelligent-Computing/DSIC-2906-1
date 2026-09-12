import numpy as np
from src.groundtruth.exact_filtered_knn import exact_filtered_knn


def test_exact_filtered_knn_respects_mask():
    base = np.array([[1.,0.],[0.9,0.1],[0.,1.]], dtype=float)
    q = np.array([1.,0.])
    ids = exact_filtered_knn(base, q, np.array([False, True, True]), k=1)
    assert ids.tolist() == [1]
