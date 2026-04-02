"""パイプライン概況統計."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from config import AppConfig
from salesforce.data_extractor import DealType

logger = logging.getLogger(__name__)


class PipelineAnalyzer:
    """パイプライン全体の統計サマリーを生成."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def summarize(
        self,
        opportunities: list[dict[str, Any]],
        closed_won: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """パイプラインサマリーを辞書で返す."""
        today = date.today()
        closed_won = closed_won or []

        total_pipeline = sum(o["amount"] for o in opportunities)
        confirmed_revenue = sum(o["amount"] for o in closed_won)

        new_deals = [o for o in opportunities if o["deal_type"] == DealType.NEW]
        existing_deals = [o for o in opportunities if o["deal_type"] == DealType.EXISTING]

        avg_deal_size = total_pipeline / len(opportunities) if opportunities else 0
        avg_age_days = (
            sum((today - o["created_date"]).days for o in opportunities) / len(opportunities)
            if opportunities
            else 0
        )

        # ステージ別集計
        stage_summary: dict[str, dict[str, Any]] = {}
        for opp in opportunities:
            stage = opp["stage"]
            if stage not in stage_summary:
                stage_summary[stage] = {"count": 0, "amount": 0}
            stage_summary[stage]["count"] += 1
            stage_summary[stage]["amount"] += opp["amount"]

        # 担当者別集計
        owner_summary: dict[str, dict[str, Any]] = {}
        for opp in opportunities:
            owner = opp["owner_name"]
            if owner not in owner_summary:
                owner_summary[owner] = {"count": 0, "amount": 0}
            owner_summary[owner]["count"] += 1
            owner_summary[owner]["amount"] += opp["amount"]

        # 今月クローズ予定
        this_month_opps = [
            o for o in opportunities
            if o["close_date"].year == today.year and o["close_date"].month == today.month
        ]

        return {
            "date": today,
            "total_pipeline": total_pipeline,
            "confirmed_revenue": confirmed_revenue,
            "total_deals": len(opportunities),
            "new_deal_count": len(new_deals),
            "new_deal_amount": sum(o["amount"] for o in new_deals),
            "existing_deal_count": len(existing_deals),
            "existing_deal_amount": sum(o["amount"] for o in existing_deals),
            "avg_deal_size": int(avg_deal_size),
            "avg_age_days": round(avg_age_days, 1),
            "stage_summary": stage_summary,
            "owner_summary": owner_summary,
            "this_month_deals": len(this_month_opps),
            "this_month_amount": sum(o["amount"] for o in this_month_opps),
        }
