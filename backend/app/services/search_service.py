"""
NotingHill — services/search_service.py
"""
from __future__ import annotations
from . import llm_service
from ..db import repo_items, repo_search

SEARCH_KEYS = (
    "file_type_group", "extension", "root_id",
    "min_size", "max_size", "since_ts", "until_ts",
    "order_by", "limit", "offset",
    "folder_path", "search_content",
)


def search(query: str, **filters) -> list[dict]:
    search_filters = {k: v for k, v in filters.items() if k in SEARCH_KEYS}
    return repo_search.fts_search(query, **search_filters)


def ask(query: str, **filters) -> dict:
    effective_filters = {k: v for k, v in filters.items() if k in SEARCH_KEYS}
    search_limit = effective_filters.get("limit") or 20
    effective_filters["limit"] = min(int(search_limit), 50)
    results = search(query=query, **effective_filters)
    llm = llm_service.answer_search_question(query, results)
    return {"query": query, "count": len(results), "results": results, "llm": llm}


def get_preview(item_id: int) -> dict | None:
    item = repo_items.get_item(item_id)
    if not item:
        return None
    from ..db.connection import get_db
    with get_db() as con:
        dups = con.execute(
            """SELECT dgi.group_id, dg.group_type, dg.item_count
               FROM duplicate_group_items dgi
               JOIN duplicate_groups dg ON dg.group_id=dgi.group_id
               WHERE dgi.item_id=?""",
            (item_id,),
        ).fetchall()
    item["duplicate_info"] = [dict(d) for d in dups]
    return item
