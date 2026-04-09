"""
NotingHill — api/routes_vfolders.py
Virtual folder CRUD + item membership endpoints.
"""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..db import repo_vfolders

router = APIRouter(prefix="/api/vfolders", tags=["vfolders"])


# ── Pydantic models ──────────────────────────────────────────

class FolderCreate(BaseModel):
    name: str
    parent_vf_id: Optional[int] = None
    color: str = "#67e8f9"
    icon: str = "📁"


class FolderUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    parent_vf_id: Optional[int] = None  # None = move to root


class ItemAdd(BaseModel):
    item_id: int


# ── Folder endpoints ─────────────────────────────────────────

@router.get("")
def list_folders():
    """Return all folders flat with item_count."""
    return {"folders": repo_vfolders.list_all_folders()}


@router.post("")
def create_folder(body: FolderCreate):
    folder = repo_vfolders.create_folder(
        name=body.name,
        parent_vf_id=body.parent_vf_id,
        color=body.color,
        icon=body.icon,
    )
    return folder


@router.patch("/{vf_id}")
def update_folder(vf_id: int, body: FolderUpdate):
    # -1 sentinel means "don't change parent"; None means "move to root"
    parent_sentinel = -1 if body.parent_vf_id is None and "parent_vf_id" not in body.model_fields_set else body.parent_vf_id
    folder = repo_vfolders.update_folder(
        vf_id=vf_id,
        name=body.name,
        color=body.color,
        icon=body.icon,
        parent_vf_id=parent_sentinel,
    )
    if not folder:
        raise HTTPException(404, "Virtual folder not found")
    return folder


@router.delete("/{vf_id}")
def delete_folder(vf_id: int):
    ok = repo_vfolders.delete_folder(vf_id)
    if not ok:
        raise HTTPException(404, "Virtual folder not found")
    return {"ok": True}


# ── Item membership endpoints ────────────────────────────────

@router.get("/{vf_id}/items")
def get_folder_items(vf_id: int, limit: int = 200, offset: int = 0):
    items = repo_vfolders.get_folder_items(vf_id, limit=limit, offset=offset)
    return {"items": items, "count": len(items)}


@router.post("/{vf_id}/items")
def add_item_to_folder(vf_id: int, body: ItemAdd):
    folder = repo_vfolders.get_folder(vf_id)
    if not folder:
        raise HTTPException(404, "Virtual folder not found")
    repo_vfolders.add_item(vf_id, body.item_id)
    return {"ok": True}


@router.delete("/{vf_id}/items/{item_id}")
def remove_item_from_folder(vf_id: int, item_id: int):
    repo_vfolders.remove_item(vf_id, item_id)
    return {"ok": True}


@router.get("/item/{item_id}/folders")
def get_item_folders(item_id: int):
    """Which virtual folders does this item belong to?"""
    return {"folders": repo_vfolders.get_item_folders(item_id)}
