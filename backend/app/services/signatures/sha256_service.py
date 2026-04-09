"""
NotingHill — services/signatures/sha256_service.py
"""
import hashlib
from pathlib import Path


def compute_sha256(path: Path, chunk_size: int = 65536) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None
