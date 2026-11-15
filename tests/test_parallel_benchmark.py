"""Benchmark paralel (P5, DT-7) pada data sintetis dengan satu pekerja (tanpa fork)."""
import pandas as pd

from src.benchmark.main_benchmark import method_configs
from src.benchmark import parallel_benchmark as pb
from tests.test_main_benchmark import _cfg, _data


def _siap():
    corpus, v, nb, wl, gt = _data()
    pb._siapkan(corpus, v, nb, 0, wl, gt, 10)
    return method_configs(_cfg())


def test_throughput_satu_baris_per_konfigurasi():
    configs = _siap()
    r = pd.DataFrame(pb.run_throughput(configs, workers=1, timeout_ms=None))
    assert len(r) == len(configs) and (r["qps"] > 0).all() and (r["timeout_pct"] == 0).all()


def test_stabilitas_tanpa_timeout_identik():
    configs = _siap()
    log = pd.DataFrame(pb.run_stability(configs, workers=1, copies=2, timeout_ms=None))
    assert len(log) == 2 * 2 * len(configs)
    s = pb.stability_summary(log)
    assert (s["identik_pct"] == 100).all() and (s["timeout_pct"] == 0).all()
