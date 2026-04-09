"""
NotingHill — services/signatures/phash_service.py
Perceptual hash (pHash) for image near-duplicate detection.
"""
from pathlib import Path


def compute_phash(path: Path) -> str | None:
    try:
        from PIL import Image
        import math

        size = 32
        small_size = 8

        with Image.open(str(path)) as img:
            img = img.convert("L").resize((size, size), Image.LANCZOS)
            pixels = list(img.getdata())

        # DCT-based pHash
        dct = _dct_2d(pixels, size)
        dct_low = [dct[i * size + j] for i in range(small_size) for j in range(small_size)]
        dct_low = dct_low[1:]  # exclude DC component

        avg = sum(dct_low) / len(dct_low)
        bits = "".join("1" if val > avg else "0" for val in dct_low)
        hash_int = int(bits, 2)
        return format(hash_int, '016x')
    except ImportError:
        return None
    except Exception:
        return None


def _dct_2d(pixels: list, size: int) -> list[float]:
    import math
    matrix = [pixels[i*size:(i+1)*size] for i in range(size)]
    result = []
    for u in range(size):
        for v in range(size):
            val = 0.0
            for x in range(size):
                for y in range(size):
                    val += (matrix[x][y] *
                            math.cos(math.pi * u * (2*x+1) / (2*size)) *
                            math.cos(math.pi * v * (2*y+1) / (2*size)))
            result.append(val)
    return result


def phash_distance(h1: str, h2: str) -> int:
    try:
        xor = int(h1, 16) ^ int(h2, 16)
        return bin(xor).count('1')
    except Exception:
        return 64


def phash_similarity(h1: str, h2: str) -> float:
    if not h1 or not h2:
        return 0.0
    dist = phash_distance(h1, h2)
    return 1.0 - dist / 64.0
