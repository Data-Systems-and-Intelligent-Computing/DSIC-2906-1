# ---------------------------------------------------------------
# Lingkungan DiskANN untuk DSIC-2906-1
# diskannpy 0.7.0 hanya tersedia untuk Linux x86_64 + Python 3.9-3.11,
# sehingga di Mac (Apple Silicon) dijalankan lewat emulasi linux/amd64.
# Embedding tetap dibuat di Mac (venv), hasil .npy dibaca di container.
# ---------------------------------------------------------------
FROM --platform=linux/amd64 python:3.11-slim

# Folder kerja = root repo yang di-mount dari laptop
WORKDIR /workspace

# Library yang dibutuhkan untuk indeks, benchmark, dan test
RUN pip install --no-cache-dir \
        diskannpy==0.7.0 \
        "pandas>=2.2" \
        "pyarrow>=16" \
        "pyyaml>=6.0" \
        "psutil>=5.9" \
        "pytest>=8.2"

# Reproducibility (sesuai .env.example)
ENV PYTHONHASHSEED=0 \
    OMP_NUM_THREADS=1

CMD ["bash"]
