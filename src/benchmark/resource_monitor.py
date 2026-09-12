"""Lightweight CPU/RAM observation helpers; hard limits should use cgroup/VM controls."""
from __future__ import annotations
import psutil


def snapshot() -> dict:
    proc = psutil.Process()
    return {"rss_bytes": proc.memory_info().rss, "cpu_percent": proc.cpu_percent(interval=None)}
