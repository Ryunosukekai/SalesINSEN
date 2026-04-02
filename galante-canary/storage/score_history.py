"""Save and query churn score history."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from storage.db import get_connection

logger = logging.getLogger(__name__)


def save_score(result: dict[str, Any]) -> None:
    """Persist a single scored account result."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO score_history
                (account_id, account_name, owner_name, score, label,
                 signals, prescription, trend, scanned_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result["account_id"],
                result["account_name"],
                result.get("owner_name", ""),
                result["score"],
                result["label"],
                json.dumps(result.get("signals", []), ensure_ascii=False),
                json.dumps(result.get("prescription", {}), ensure_ascii=False),
                json.dumps(result.get("trend", {}), ensure_ascii=False),
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )


def save_scores(results: list[dict[str, Any]]) -> None:
    """Persist all scored account results in one transaction."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    rows = [
        (
            r["account_id"],
            r["account_name"],
            r.get("owner_name", ""),
            r["score"],
            r["label"],
            json.dumps(r.get("signals", []), ensure_ascii=False),
            json.dumps(r.get("prescription", {}), ensure_ascii=False),
            json.dumps(r.get("trend", {}), ensure_ascii=False),
            now_str,
        )
        for r in results
    ]
    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO score_history
                (account_id, account_name, owner_name, score, label,
                 signals, prescription, trend, scanned_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
    logger.info("スコア履歴を保存しました: %d件", len(rows))


def get_score_history(
    account_id: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return recent score history for an account (newest first)."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT account_id, account_name, score, label, signals,
                   prescription, trend, scanned_at
            FROM score_history
            WHERE account_id = ?
            ORDER BY scanned_at DESC
            LIMIT ?
            """,
            (account_id, limit),
        )
        rows = cursor.fetchall()

    results: list[dict[str, Any]] = []
    for row in rows:
        results.append({
            "account_id": row["account_id"],
            "account_name": row["account_name"],
            "score": row["score"],
            "label": row["label"],
            "signals": json.loads(row["signals"]),
            "prescription": json.loads(row["prescription"]),
            "trend": json.loads(row["trend"]),
            "scanned_at": row["scanned_at"],
        })
    return results


def save_scan_run(
    total_accounts: int,
    avg_score: float,
    max_score: int,
    alert_sent: bool,
) -> int:
    """Record a completed scan run. Returns the run ID."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO scan_runs
                (total_accounts, avg_score, max_score, alert_sent,
                 started_at, finished_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (total_accounts, avg_score, max_score, int(alert_sent), now_str, now_str),
        )
        return cursor.lastrowid  # type: ignore[return-value]


def get_recent_runs(limit: int = 10) -> list[dict[str, Any]]:
    """Return recent scan runs."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT id, total_accounts, avg_score, max_score,
                   alert_sent, started_at, finished_at
            FROM scan_runs
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()

    return [
        {
            "id": row["id"],
            "total_accounts": row["total_accounts"],
            "avg_score": row["avg_score"],
            "max_score": row["max_score"],
            "alert_sent": bool(row["alert_sent"]),
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
        }
        for row in rows
    ]
