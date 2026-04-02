"""SQLite データベースセットアップ・基本操作."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS forecast_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date   TEXT    NOT NULL,
    report_type     TEXT    NOT NULL DEFAULT 'daily',
    confirmed       INTEGER NOT NULL DEFAULT 0,
    weighted        INTEGER NOT NULL DEFAULT 0,
    optimistic      INTEGER NOT NULL DEFAULT 0,
    pessimistic     INTEGER NOT NULL DEFAULT 0,
    pipeline_total  INTEGER NOT NULL DEFAULT 0,
    deal_count      INTEGER NOT NULL DEFAULT 0,
    gap_min         INTEGER NOT NULL DEFAULT 0,
    gap_max         INTEGER NOT NULL DEFAULT 0,
    alerts_count    INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS monthly_actuals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    year_month      TEXT    NOT NULL UNIQUE,
    actual_revenue  INTEGER NOT NULL DEFAULT 0,
    forecast_weighted INTEGER NOT NULL DEFAULT 0,
    deals_won       INTEGER NOT NULL DEFAULT 0,
    deals_lost      INTEGER NOT NULL DEFAULT 0,
    close_rate      REAL    NOT NULL DEFAULT 0.0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS pipeline_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date   TEXT    NOT NULL,
    pipeline_total  INTEGER NOT NULL DEFAULT 0,
    deal_count      INTEGER NOT NULL DEFAULT 0,
    new_deal_count  INTEGER NOT NULL DEFAULT 0,
    existing_deal_count INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""


class Database:
    """SQLite データベースマネージャー."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        """DB ファイルに接続し、スキーマを初期化."""
        path = Path(self._db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        logger.info("SQLite 接続: %s", self._db_path)

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self.connect()
        assert self._conn is not None
        return self._conn

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def executemany(self, sql: str, params_list: list[tuple]) -> None:
        self.conn.executemany(sql, params_list)

    def commit(self) -> None:
        self.conn.commit()

    def fetchall(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        cursor = self.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def fetchone(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        cursor = self.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
