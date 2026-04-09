"""
NotingHill — db/connection.py
SQLite connection manager with WAL mode and lightweight schema migrations.
"""
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

_local = threading.local()
DB_PATH: Path | None = None


_INDEX_JOB_MIGRATIONS = [
    ("pending_count", "ALTER TABLE index_jobs ADD COLUMN pending_count INTEGER NOT NULL DEFAULT 0"),
    ("scan_complete", "ALTER TABLE index_jobs ADD COLUMN scan_complete INTEGER NOT NULL DEFAULT 0"),
    ("current_file", "ALTER TABLE index_jobs ADD COLUMN current_file TEXT"),
    ("updated_ts", "ALTER TABLE index_jobs ADD COLUMN updated_ts INTEGER"),
]


def init_db(db_path: Path) -> None:
    global DB_PATH
    DB_PATH = db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path = Path(__file__).parent / "schema.sql"
    with _connect(db_path) as con:
        con.executescript(schema_path.read_text(encoding="utf-8"))
        _apply_migrations(con)
        _migrate_virtual_folders(con)
        con.commit()



def _connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path), check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA synchronous=NORMAL")
    return con



def _column_exists(con: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    rows = con.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)



def _apply_migrations(con: sqlite3.Connection) -> None:
    for column_name, sql in _INDEX_JOB_MIGRATIONS:
        if not _column_exists(con, "index_jobs", column_name):
            con.execute(sql)


@contextmanager
def get_db():
    """Thread-local connection context manager."""
    if not hasattr(_local, "con") or _local.con is None:
        _local.con = _connect(DB_PATH)
    try:
        yield _local.con
    except Exception:
        _local.con.rollback()
        raise



def close_thread_db() -> None:
    if hasattr(_local, "con") and _local.con:
        _local.con.close()
        _local.con = None


def _migrate_virtual_folders(con: sqlite3.Connection) -> None:
    """Create virtual folder tables if they don't exist (for existing DBs)."""
    con.executescript("""
        CREATE TABLE IF NOT EXISTS virtual_folders (
          vf_id        INTEGER PRIMARY KEY AUTOINCREMENT,
          parent_vf_id INTEGER REFERENCES virtual_folders(vf_id) ON DELETE CASCADE,
          name         TEXT NOT NULL,
          color        TEXT DEFAULT '#67e8f9',
          icon         TEXT DEFAULT '📁',
          created_ts   INTEGER NOT NULL,
          updated_ts   INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_vf_parent ON virtual_folders(parent_vf_id);
        CREATE TABLE IF NOT EXISTS virtual_folder_items (
          vf_item_id   INTEGER PRIMARY KEY AUTOINCREMENT,
          vf_id        INTEGER NOT NULL REFERENCES virtual_folders(vf_id) ON DELETE CASCADE,
          item_id      INTEGER NOT NULL REFERENCES items(item_id) ON DELETE CASCADE,
          added_ts     INTEGER NOT NULL,
          UNIQUE(vf_id, item_id)
        );
        CREATE INDEX IF NOT EXISTS idx_vfi_vf_id   ON virtual_folder_items(vf_id);
        CREATE INDEX IF NOT EXISTS idx_vfi_item_id ON virtual_folder_items(item_id);
    """)
    con.commit()
