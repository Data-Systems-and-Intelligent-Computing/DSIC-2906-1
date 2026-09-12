"""AdaptiveL search helpers based on Liu et al. (2026), Algorithms 2 and 3."""
from __future__ import annotations
import math


def compute_adaptive_multiplier(sp_hat: float, m_max: float) -> float:
    if not 0.0 <= sp_hat <= 1.0:
        raise ValueError("sp_hat must be in [0, 1]")
    if m_max < 1:
        raise ValueError("m_max must be >= 1")
    if sp_hat == 0:
        return float(m_max)
    if sp_hat >= 0.5:
        return 1.0
    if sp_hat >= 0.1:
        return min(float(m_max), 2.0)
    l = -math.log10(sp_hat)
    return min(float(m_max), 2.0 ** l)


def adaptivel_search(*args, **kwargs):
    raise NotImplementedError("Integrate AdaptiveL into the verified DiskANN traversal implementation.")
