"""SQLite database operations for Galante Canary."""
from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from config import DB_PATH

logger = logging.getLogger(__name__)

_SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS score_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id  TEXT    NOT NULL,
    account_name TEXT   NOT NULL,
    owner_name  TEXT    NOT NULL DEFAULT '',
    score       INTEGER NOT NULL,
    label       TEXT    NOT NULL,
    signals     TEXT    NOT NULL DEFAULT '[]',
    prescription TEXT   NOT NULL DEFAULT '{}',
    trend       TEXT    NOT NULL DEFAULT '{}',
    scanned_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sh_account ON score_history(account_id);
CREATE INDEX IF NOT EXISTS idx_sh_scanned ON score_history(scanned_at);

CREATE TABLE IF NOT EXISTS scan_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    total_accounts INTEGER NOT NULL,
    avg_score   REAL    NOT NULL DEFAULT 0,
    max_score   INTEGER NOT NULL DEFAULT 0,
    alert_sent  INTEGER NOT NULL DEFAULT 0,
    started_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT
);
"""


def _ensure_dir() -> None:
    """Ensure the parent directory of the DB file exists."""
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    """Create tables and indexes if they don't exist."""
    _ensure_dir()
    with get_connection() as conn:
        conn.executescript(_SCHEMA_SQL)
    logger.info("データベース初期化完了: %s", DB_PATH)


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Yield a SQLite connection with WAL mode enabled."""
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
