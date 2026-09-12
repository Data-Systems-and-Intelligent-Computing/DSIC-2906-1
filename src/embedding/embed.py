"""Embedding entry point. Main benchmark must use one frozen model/configuration."""
from __future__ import annotations
from pathlib import Path
import yaml


def load_embedding_config(path: str = "configs/embedding.yaml") -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    cfg = load_embedding_config()
    print("Embedding configuration loaded:", cfg["model_name"])
    print("Implement corpus I/O for the frozen project dataset before running final benchmark.")


if __name__ == "__main__":
    main()
