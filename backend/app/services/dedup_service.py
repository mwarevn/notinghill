"""
NotingHill — services/dedup_service.py
Exact duplicate detection (sha256) + near-duplicate (simhash/phash).
"""
from ..db.connection import get_db
from ..db import repo_duplicates
from ..services.signatures.simhash_service import similarity as simhash_sim
from ..services.signatures.phash_service import phash_similarity


def run_exact_dedup():
    """Group files with identical sha256."""
    with get_db() as con:
        rows = con.execute("""
            SELECT sha256, GROUP_CONCAT(item_id) as ids
            FROM items WHERE sha256 IS NOT NULL AND is_deleted=0
            GROUP BY sha256 HAVING COUNT(*)>1
        """).fetchall()

    for row in rows:
        sha = row["sha256"]
        ids = [int(i) for i in row["ids"].split(",")]
        repo_duplicates.upsert_duplicate_group("exact", sha, ids)


def run_text_dedup(threshold: float = 0.90):
    """Group files with similar simhash (hamming distance < 7 of 64 bits)."""
    with get_db() as con:
        rows = con.execute("""
            SELECT item_id, simhash64 FROM items
            WHERE simhash64 IS NOT NULL AND is_deleted=0
        """).fetchall()

    items = [(r["item_id"], r["simhash64"]) for r in rows]
    visited = set()
    groups = []

    for i, (id_a, h_a) in enumerate(items):
        if id_a in visited:
            continue
        group = [id_a]
        scores = {id_a: 1.0}
        for id_b, h_b in items[i+1:]:
            if id_b in visited:
                continue
            sim = simhash_sim(h_a, h_b)
            if sim >= threshold:
                group.append(id_b)
                scores[id_b] = sim
        if len(group) > 1:
            visited.update(group)
            groups.append((group, scores))

    for group, scores in groups:
        key = f"simhash_{min(group)}"
        repo_duplicates.upsert_duplicate_group("similar_text", key, group, scores)


def run_image_dedup(threshold: float = 0.90):
    """Group images with similar perceptual hash."""
    with get_db() as con:
        rows = con.execute("""
            SELECT item_id, phash FROM items
            WHERE phash IS NOT NULL AND is_deleted=0 AND file_type_group='image'
        """).fetchall()

    items = [(r["item_id"], r["phash"]) for r in rows]
    visited = set()
    groups = []

    for i, (id_a, h_a) in enumerate(items):
        if id_a in visited:
            continue
        group = [id_a]
        scores = {id_a: 1.0}
        for id_b, h_b in items[i+1:]:
            if id_b in visited:
                continue
            sim = phash_similarity(h_a, h_b)
            if sim >= threshold:
                group.append(id_b)
                scores[id_b] = sim
        if len(group) > 1:
            visited.update(group)
            groups.append((group, scores))

    for group, scores in groups:
        key = f"phash_{min(group)}"
        repo_duplicates.upsert_duplicate_group("similar_image", key, group, scores)
