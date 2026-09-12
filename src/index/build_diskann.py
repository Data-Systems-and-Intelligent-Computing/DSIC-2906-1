"""DiskANN index build adapter.

Use the official/instrumented DiskANN implementation selected by the project.
Do not silently substitute HNSW/FAISS while reporting results as DiskANN.
"""
from __future__ import annotations
from pathlib import Path
import yaml


def main() -> None:
    cfg = yaml.safe_load(Path("configs/diskann.yaml").read_text(encoding="utf-8"))
    raise SystemExit(
        "DiskANN binding/build integration is environment-specific. "
        f"Configure the verified implementation for R={cfg['R']}, L_build={cfg['L_build']}."
    )


if __name__ == "__main__":
    main()
