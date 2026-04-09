"""
NotingHill — services/signatures/simhash_service.py
Lightweight 64-bit simhash for near-duplicate text detection.
No external deps needed.
"""
import hashlib
import re


def _shingles(text: str, k: int = 3) -> list[str]:
    tokens = re.findall(r'\w+', text.lower())
    if len(tokens) < k:
        return tokens
    return [" ".join(tokens[i:i+k]) for i in range(len(tokens)-k+1)]


def compute_simhash(text: str) -> str | None:
    if not text or len(text) < 20:
        return None
    try:
        v = [0] * 64
        for shingle in _shingles(text):
            h = int(hashlib.md5(shingle.encode()).hexdigest(), 16)
            for i in range(64):
                bit = (h >> i) & 1
                v[i] += 1 if bit else -1
        fingerprint = 0
        for i in range(64):
            if v[i] > 0:
                fingerprint |= (1 << i)
        return format(fingerprint, '016x')
    except Exception:
        return None


def hamming_distance(h1: str, h2: str) -> int:
    try:
        xor = int(h1, 16) ^ int(h2, 16)
        return bin(xor).count('1')
    except Exception:
        return 64


def similarity(h1: str, h2: str) -> float:
    """Returns 0.0-1.0, 1.0 = identical."""
    if not h1 or not h2:
        return 0.0
    dist = hamming_distance(h1, h2)
    return 1.0 - dist / 64.0
