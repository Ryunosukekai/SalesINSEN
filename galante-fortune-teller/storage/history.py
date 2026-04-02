"""予測履歴の保存・取得 — トレンド分析用."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from storage.db import Database

logger = logging.getLogger(__name__)


class ForecastHistory:
    """予測スナップショットの保存と取得."""

    def __init__(self, db: Database) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # 保存
    # ------------------------------------------------------------------
    def save_snapshot(
        self,
        snapshot_date: date,
        report_type: str,
        forecast: dict[str, Any],
        alerts_count: int,
    ) -> None:
        """日次/週次/月次のスナップショットを保存."""
        current = forecast.get("current_month", {})
        self._db.execute(
            """
            INSERT INTO forecast_snapshots
                (snapshot_date, report_type, confirmed, weighted, optimistic,
                 pessimistic, pipeline_total, deal_count, gap_min, gap_max, alerts_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_date.isoformat(),
                report_type,
                current.get("confirmed", 0),
                current.get("weighted", 0),
                current.get("optimistic", 0),
                current.get("pessimistic", 0),
                current.get("pipeline_total", 0),
                current.get("deal_count", 0),
                current.get("gap_min", 0),
                current.get("gap_max", 0),
                alerts_count,
            ),
        )
        self._db.commit()
        logger.info("スナップショット保存: %s (%s)", snapshot_date, report_type)

    def save_pipeline_snapshot(
        self,
        snapshot_date: date,
        pipeline_summary: dict[str, Any],
    ) -> None:
        """パイプライン履歴を保存."""
        self._db.execute(
            """
            INSERT INTO pipeline_history
                (snapshot_date, pipeline_total, deal_count, new_deal_count, existing_deal_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                snapshot_date.isoformat(),
                pipeline_summary.get("total_pipeline", 0),
                pipeline_summary.get("total_deals", 0),
                pipeline_summary.get("new_deal_count", 0),
                pipeline_summary.get("existing_deal_count", 0),
            ),
        )
        self._db.commit()

    def save_monthly_actual(
        self,
        year_month: str,
        actual_revenue: int,
        forecast_weighted: int,
        deals_won: int,
        deals_lost: int,
        close_rate: float,
    ) -> None:
        """月次実績を保存（UPSERT）."""
        self._db.execute(
            """
            INSERT INTO monthly_actuals
                (year_month, actual_revenue, forecast_weighted, deals_won, deals_lost, close_rate)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(year_month) DO UPDATE SET
                actual_revenue = excluded.actual_revenue,
                forecast_weighted = excluded.forecast_weighted,
                deals_won = excluded.deals_won,
                deals_lost = excluded.deals_lost,
                close_rate = excluded.close_rate
            """,
            (year_month, actual_revenue, forecast_weighted, deals_won, deals_lost, close_rate),
        )
        self._db.commit()

    # ------------------------------------------------------------------
    # 取得
    # ------------------------------------------------------------------
    def get_recent_snapshots(self, days: int = 30) -> list[dict[str, Any]]:
        """直近N日のスナップショットを取得."""
        return self._db.fetchall(
            """
            SELECT * FROM forecast_snapshots
            WHERE snapshot_date >= date('now', ?)
            ORDER BY snapshot_date ASC
            """,
            (f"-{days} days",),
        )

    def get_pipeline_history(self, days: int = 60) -> list[dict[str, Any]]:
        """パイプライン推移を取得."""
        return self._db.fetchall(
            """
            SELECT * FROM pipeline_history
            WHERE snapshot_date >= date('now', ?)
            ORDER BY snapshot_date ASC
            """,
            (f"-{days} days",),
        )

    def get_monthly_actuals(self, months: int = 12) -> list[dict[str, Any]]:
        """月次実績の履歴を取得."""
        return self._db.fetchall(
            """
            SELECT * FROM monthly_actuals
            ORDER BY year_month DESC
            LIMIT ?
            """,
            (months,),
        )

    def get_close_rate_trend(self, weeks: int = 4) -> list[float]:
        """週次成約率トレンドを取得.

        スナップショットがない場合はベースラインレートを返す。
        """
        rows = self._db.fetchall(
            """
            SELECT
                strftime('%Y-W%W', snapshot_date) as week,
                AVG(CAST(weighted AS REAL) / NULLIF(pipeline_total, 0)) as rate
            FROM forecast_snapshots
            WHERE snapshot_date >= date('now', ?)
              AND pipeline_total > 0
            GROUP BY week
            ORDER BY week DESC
            LIMIT ?
            """,
            (f"-{weeks * 7} days", weeks),
        )
        rates = [r["rate"] for r in reversed(rows) if r["rate"] is not None]
        return rates if rates else [0.104]  # フォールバック: ベースライン成約率
