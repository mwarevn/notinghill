"""
NotingHill — db/repo_vfolders.py
CRUD for virtual folders (tree) + file membership.
"""
from __future__ import annotations
import time
from .connection import get_db


# ── Folder CRUD ─────────────────────────────────────────────

def create_folder(name: str, parent_vf_id: int | None = None,
                  color: str = "#67e8f9", icon: str = "📁") -> dict:
    now = int(time.time())
    with get_db() as con:
        cur = con.execute(
            """INSERT INTO virtual_folders(parent_vf_id, name, color, icon, created_ts, updated_ts)
               VALUES(?,?,?,?,?,?)""",
            (parent_vf_id, name, color, icon, now, now),
        )
        con.commit()
        return get_folder(cur.lastrowid)


def get_folder(vf_id: int) -> dict | None:
    with get_db() as con:
        row = con.execute(
            "SELECT * FROM virtual_folders WHERE vf_id=?", (vf_id,)
        ).fetchone()
        return dict(row) if row else None


def update_folder(vf_id: int, name: str = None, color: str = None,
                  icon: str = None, parent_vf_id: int | None = -1) -> dict | None:
    now = int(time.time())
    with get_db() as con:
        row = con.execute("SELECT * FROM virtual_folders WHERE vf_id=?", (vf_id,)).fetchone()
        if not row:
            return None
        r = dict(row)
        new_name   = name   if name   is not None else r["name"]
        new_color  = color  if color  is not None else r["color"]
        new_icon   = icon   if icon   is not None else r["icon"]
        new_parent = r["parent_vf_id"] if parent_vf_id == -1 else parent_vf_id
        con.execute(
            """UPDATE virtual_folders
               SET name=?, color=?, icon=?, parent_vf_id=?, updated_ts=?
               WHERE vf_id=?""",
            (new_name, new_color, new_icon, new_parent, now, vf_id),
        )
        con.commit()
        return get_folder(vf_id)


def delete_folder(vf_id: int) -> bool:
    """Delete folder and all descendants (CASCADE handles children)."""
    with get_db() as con:
        cur = con.execute("DELETE FROM virtual_folders WHERE vf_id=?", (vf_id,))
        con.commit()
        return cur.rowcount > 0


def list_all_folders() -> list[dict]:
    """Return all folders flat; frontend builds the tree."""
    with get_db() as con:
        rows = con.execute(
            """SELECT vf.*, COUNT(vfi.vf_item_id) AS item_count
               FROM virtual_folders vf
               LEFT JOIN virtual_folder_items vfi ON vfi.vf_id=vf.vf_id
               GROUP BY vf.vf_id
               ORDER BY vf.parent_vf_id NULLS FIRST, vf.name"""
        ).fetchall()
        return [dict(r) for r in rows]


# ── Item membership ──────────────────────────────────────────

def add_item(vf_id: int, item_id: int) -> bool:
    now = int(time.time())
    with get_db() as con:
        try:
            con.execute(
                "INSERT OR IGNORE INTO virtual_folder_items(vf_id, item_id, added_ts) VALUES(?,?,?)",
                (vf_id, item_id, now),
            )
            con.commit()
            return True
        except Exception:
            return False


def remove_item(vf_id: int, item_id: int) -> bool:
    with get_db() as con:
        cur = con.execute(
            "DELETE FROM virtual_folder_items WHERE vf_id=? AND item_id=?",
            (vf_id, item_id),
        )
        con.commit()
        return cur.rowcount > 0


def get_folder_items(vf_id: int, limit: int = 200, offset: int = 0) -> list[dict]:
    with get_db() as con:
        rows = con.execute(
            """SELECT i.item_id, i.file_name, i.full_path, i.extension,
                      i.file_type_group, i.size_bytes, i.modified_ts, i.best_time_ts,
                      ic.content_preview, vfi.added_ts
               FROM virtual_folder_items vfi
               JOIN items i ON i.item_id=vfi.item_id
               LEFT JOIN item_content ic ON ic.item_id=i.item_id
               WHERE vfi.vf_id=? AND i.is_deleted=0
               ORDER BY vfi.added_ts DESC
               LIMIT ? OFFSET ?""",
            (vf_id, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


def get_item_folders(item_id: int) -> list[dict]:
    """Which virtual folders does this item belong to?"""
    with get_db() as con:
        rows = con.execute(
            """SELECT vf.vf_id, vf.name, vf.color, vf.icon
               FROM virtual_folder_items vfi
               JOIN virtual_folders vf ON vf.vf_id=vfi.vf_id
               WHERE vfi.item_id=?""",
            (item_id,),
        ).fetchall()
        return [dict(r) for r in rows]
