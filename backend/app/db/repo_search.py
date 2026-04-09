"""
NotingHill — db/repo_search.py
FTS5 full-text search + wildcard GLOB/LIKE + metadata field search.
"""
from __future__ import annotations
from .connection import get_db

FTS_TABLE = "fts_items"


def fts_index_item(item_id: int, file_name: str, full_path: str,
                   extracted_text: str = "", title: str = ""):
    with get_db() as con:
        con.execute(f"DELETE FROM {FTS_TABLE} WHERE rowid=? OR item_id=?", (item_id, item_id))
        con.execute(
            f"""INSERT INTO {FTS_TABLE}(rowid, item_id, file_name, full_path, extracted_text, meta_title)
                VALUES(?,?,?,?,?,?)""",
            (item_id, item_id, file_name, full_path, extracted_text or "", title or ""),
        )
        con.commit()


def _has_wildcard(q: str) -> bool:
    return "*" in q or "?" in q


def _to_glob(q: str) -> str:
    if not _has_wildcard(q):
        return f"*{q}*"
    return q


def _to_like(q: str) -> str:
    if not _has_wildcard(q):
        return f"%{q}%"
    return q.replace("*", "%").replace("?", "_")


def _base_filters(file_type_group, extension, root_id, min_size, max_size,
                  since_ts, until_ts, folder_path):
    clauses = ["i.is_deleted=0"]
    params = []
    if file_type_group:
        clauses.append("i.file_type_group=?")
        params.append(file_type_group)
    if extension:
        clauses.append("i.extension=?")
        params.append(extension)
    if root_id:
        clauses.append("i.root_id=?")
        params.append(root_id)
    if min_size is not None:
        clauses.append("i.size_bytes>=?")
        params.append(min_size)
    if max_size is not None:
        clauses.append("i.size_bytes<=?")
        params.append(max_size)
    if since_ts:
        clauses.append("i.best_time_ts>=?")
        params.append(since_ts)
    if until_ts:
        clauses.append("i.best_time_ts<=?")
        params.append(until_ts)
    if folder_path:
        fp_like = _to_like(folder_path) if _has_wildcard(folder_path) else f"%{folder_path}%"
        clauses.append("i.full_path LIKE ?")
        params.append(fp_like)
    return clauses, params


_SELECT = """
    SELECT i.item_id, i.file_name, i.full_path, i.extension, i.file_type_group,
           i.size_bytes, i.modified_ts, i.best_time_ts,
           ic.content_preview,
           im.title, im.artist, im.album, im.camera_model
"""


def fts_search(query: str,
               file_type_group=None, extension=None,
               root_id=None, min_size=None, max_size=None,
               since_ts=None, until_ts=None,
               folder_path=None,
               search_content: bool = False,
               order_by: str = "rank", limit: int = 50, offset: int = 0):

    if not query.strip():
        return _recent_files(file_type_group, extension, root_id, min_size, max_size,
                             since_ts, until_ts, folder_path, limit, offset)

    if _has_wildcard(query):
        return _wildcard_search(query, file_type_group, extension, root_id, min_size,
                                max_size, since_ts, until_ts, folder_path,
                                search_content, limit, offset)

    clauses, params = _base_filters(file_type_group, extension, root_id, min_size,
                                    max_size, since_ts, until_ts, folder_path)
    where_extra = (" AND " + " AND ".join(clauses)) if clauses else ""
    safe_q = query.replace('"', '""')
    fts_query = f'"{safe_q}"'
    snippet_col = f"snippet({FTS_TABLE}, 2, '<em>', '</em>', '...', 20)"

    sql = f"""
        {_SELECT},
           {snippet_col} AS snippet,
           bm25({FTS_TABLE}) AS rank
        FROM {FTS_TABLE}
        JOIN items i ON i.item_id={FTS_TABLE}.rowid
        LEFT JOIN item_content ic ON ic.item_id=i.item_id
        LEFT JOIN item_metadata im ON im.item_id=i.item_id
        WHERE {FTS_TABLE} MATCH ? {where_extra}
        ORDER BY rank
        LIMIT ? OFFSET ?
    """
    params_final = [fts_query] + params + [limit, offset]
    with get_db() as con:
        try:
            rows = con.execute(sql, params_final).fetchall()
            if rows:
                return [dict(r) for r in rows]
        except Exception:
            pass
        return _like_search(query, file_type_group, extension, root_id, min_size,
                            max_size, since_ts, until_ts, folder_path,
                            search_content, limit, offset)


def _wildcard_search(query, file_type_group, extension, root_id, min_size,
                     max_size, since_ts, until_ts, folder_path,
                     search_content, limit, offset):
    glob_pat = _to_glob(query)
    clauses, params = _base_filters(file_type_group, extension, root_id, min_size,
                                    max_size, since_ts, until_ts, folder_path)
    match_parts = [
        "i.file_name GLOB ?", "i.full_path GLOB ?",
        "COALESCE(im.title,'') GLOB ?", "COALESCE(im.artist,'') GLOB ?",
        "COALESCE(im.album,'') GLOB ?", "COALESCE(im.camera_model,'') GLOB ?",
    ]
    match_params = [glob_pat] * 6
    if search_content:
        match_parts.append("COALESCE(ic.extracted_text,'') GLOB ?")
        match_params.append(glob_pat)
    clauses.append(f"({' OR '.join(match_parts)})")
    all_params = match_params + params + [limit, offset]
    where = " AND ".join(clauses)
    sql = f"""
        {_SELECT}, i.file_name AS snippet, 0 AS rank
        FROM items i
        LEFT JOIN item_content ic ON ic.item_id=i.item_id
        LEFT JOIN item_metadata im ON im.item_id=i.item_id
        WHERE {where}
        ORDER BY i.last_indexed_ts DESC
        LIMIT ? OFFSET ?
    """
    with get_db() as con:
        rows = con.execute(sql, all_params).fetchall()
        return [dict(r) for r in rows]


def _like_search(query, file_type_group, extension, root_id, min_size,
                 max_size, since_ts, until_ts, folder_path,
                 search_content, limit, offset):
    like_pat = f"%{query}%"
    clauses, params = _base_filters(file_type_group, extension, root_id, min_size,
                                    max_size, since_ts, until_ts, folder_path)
    match_parts = [
        "i.file_name LIKE ?", "i.full_path LIKE ?",
        "COALESCE(im.title,'') LIKE ?", "COALESCE(im.artist,'') LIKE ?",
        "COALESCE(im.album,'') LIKE ?", "COALESCE(im.camera_model,'') LIKE ?",
    ]
    match_params = [like_pat] * 6
    if search_content:
        match_parts.append("COALESCE(ic.extracted_text,'') LIKE ?")
        match_params.append(like_pat)
    clauses.append(f"({' OR '.join(match_parts)})")
    all_params = match_params + params + [limit, offset]
    where = " AND ".join(clauses)
    sql = f"""
        {_SELECT}, i.file_name AS snippet, 0 AS rank
        FROM items i
        LEFT JOIN item_content ic ON ic.item_id=i.item_id
        LEFT JOIN item_metadata im ON im.item_id=i.item_id
        WHERE {where}
        ORDER BY i.last_indexed_ts DESC
        LIMIT ? OFFSET ?
    """
    with get_db() as con:
        rows = con.execute(sql, all_params).fetchall()
        return [dict(r) for r in rows]


def _recent_files(file_type_group, extension, root_id, min_size, max_size,
                  since_ts, until_ts, folder_path, limit, offset):
    clauses, params = _base_filters(file_type_group, extension, root_id, min_size,
                                    max_size, since_ts, until_ts, folder_path)
    where = " AND ".join(clauses)
    sql = f"""
        {_SELECT}, '' AS snippet, 0 AS rank
        FROM items i
        LEFT JOIN item_content ic ON ic.item_id=i.item_id
        LEFT JOIN item_metadata im ON im.item_id=i.item_id
        WHERE {where}
        ORDER BY i.last_indexed_ts DESC
        LIMIT ? OFFSET ?
    """
    params += [limit, offset]
    with get_db() as con:
        rows = con.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
