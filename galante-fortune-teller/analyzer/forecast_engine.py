"""予測エンジン — 月次着地・3ヶ月予測・逆算ロジック."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from config import AppConfig, BASELINE_METRICS
from salesforce.data_extractor import DealType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 営業日ユーティリティ
# ---------------------------------------------------------------------------
def _business_days_remaining(today: date) -> int:
    """今月の残り営業日数（土日除外）."""
    year, month = today.year, today.month
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)

    count = 0
    d = today + timedelta(days=1)
    while d <= month_end:
        if d.weekday() < 5:  # 月〜金
            count += 1
        d += timedelta(days=1)
    return max(count, 1)  # 最低1を返す


def _total_business_days(year: int, month: int) -> int:
    """指定月の総営業日数."""
    first = date(year, month, 1)
    if month == 12:
        last = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)
    count = 0
    d = first
    while d <= last:
        if d.weekday() < 5:
            count += 1
        d += timedelta(days=1)
    return max(count, 1)


def _first_of_month(base: date, offset: int) -> date:
    month = base.month + offset
    year = base.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    return date(year, month, 1)


# ---------------------------------------------------------------------------
# 予測エンジン
# ---------------------------------------------------------------------------
class ForecastEngine:
    """月次着地予測・3ヶ月アウトルック・逆算ロジック."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._fc = config.forecast

    # ------------------------------------------------------------------
    # メイン: フルレポート生成
    # ------------------------------------------------------------------
    def generate(
        self,
        opportunities: list[dict[str, Any]],
        closed_won: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """全予測データを辞書で返す."""
        today = date.today()
        closed_won = closed_won or []
        confirmed_revenue = sum(o["amount"] for o in closed_won)

        biz_days_remaining = _business_days_remaining(today)
        total_biz_days = _total_business_days(today.year, today.month)

        # 今月の着地予測
        current = self._monthly_landing(
            today, opportunities, confirmed_revenue, biz_days_remaining, total_biz_days,
        )

        # 3ヶ月予測
        three_month: list[dict[str, Any]] = []
        for offset in range(self._fc.forecast_months):
            m_start = _first_of_month(today, offset)
            m_opps = [
                o for o in opportunities
                if o["close_date"].year == m_start.year and o["close_date"].month == m_start.month
            ]
            if offset == 0:
                three_month.append(current)
            else:
                outlook = self._month_outlook(m_start, m_opps)
                three_month.append(outlook)

        # 逆算ロジック（ミニマム目標ベース）
        reverse = self._reverse_calculation(
            gap=max(0, self._fc.monthly_target_min - current["weighted"]),
            biz_days_remaining=biz_days_remaining,
        )

        return {
            "date": today,
            "biz_days_remaining": biz_days_remaining,
            "total_biz_days": total_biz_days,
            "confirmed_revenue": confirmed_revenue,
            "current_month": current,
            "three_month": three_month,
            "reverse": reverse,
        }

    # ------------------------------------------------------------------
    # 今月の着地予測
    # ------------------------------------------------------------------
    def _monthly_landing(
        self,
        today: date,
        opportunities: list[dict[str, Any]],
        confirmed: int,
        biz_days_remaining: int,
        total_biz_days: int,
    ) -> dict[str, Any]:
        """今月着地の加重・楽観・悲観予測."""
        this_month_opps = [
            o for o in opportunities
            if o["close_date"].year == today.year and o["close_date"].month == today.month
        ]

        # 加重予測: Amount × (SF確率 + ベースライン) / 2
        weighted = 0
        for opp in this_month_opps:
            base_rate = (
                self._fc.existing_deal_continue_rate
                if opp["deal_type"] == DealType.EXISTING
                else self._fc.new_deal_close_rate
            )
            blended = (opp["probability"] + base_rate) / 2.0
            weighted += opp["amount"] * blended

        # 月末ラッシュ補正: 残5営業日以内なら +5%
        rush_bonus = 0
        if biz_days_remaining <= 5:
            rush_bonus = weighted * self._fc.month_end_rush_factor

        # 残営業日補正: パイプラインの進捗度合いを考慮
        elapsed_ratio = (total_biz_days - biz_days_remaining) / total_biz_days
        biz_day_correction = weighted * (1 - elapsed_ratio) * 0.1  # 残が多いほど上振れ余地

        weighted_total = int(confirmed + weighted + rush_bonus + biz_day_correction)
        optimistic = int(weighted_total * self._fc.optimistic_multiplier)
        pessimistic = int(weighted_total * self._fc.pessimistic_multiplier)

        pipeline_total = sum(o["amount"] for o in this_month_opps)

        gap_min = max(0, self._fc.monthly_target_min - weighted_total)
        gap_max = max(0, self._fc.monthly_target_max - weighted_total)

        # ステータス判定
        if weighted_total >= self._fc.monthly_target_max:
            status = "green"
            status_emoji = "🟢"
        elif weighted_total >= self._fc.monthly_target_min:
            status = "yellow"
            status_emoji = "🟡"
        else:
            status = "red"
            status_emoji = "🔴"

        return {
            "month": _first_of_month(today, 0),
            "pipeline_total": pipeline_total,
            "confirmed": confirmed,
            "weighted": weighted_total,
            "optimistic": optimistic,
            "pessimistic": pessimistic,
            "gap_min": gap_min,
            "gap_max": gap_max,
            "status": status,
            "status_emoji": status_emoji,
            "deal_count": len(this_month_opps),
            "new_count": sum(1 for o in this_month_opps if o["deal_type"] == DealType.NEW),
            "existing_count": sum(1 for o in this_month_opps if o["deal_type"] == DealType.EXISTING),
        }

    # ------------------------------------------------------------------
    # 来月以降のアウトルック
    # ------------------------------------------------------------------
    def _month_outlook(
        self,
        month_start: date,
        opps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """来月以降の単月予測."""
        weighted = 0
        for opp in opps:
            base_rate = (
                self._fc.existing_deal_continue_rate
                if opp["deal_type"] == DealType.EXISTING
                else self._fc.new_deal_close_rate
            )
            blended = (opp["probability"] + base_rate) / 2.0
            weighted += opp["amount"] * blended

        # 新規パイプライン生成の見込み（アクティビティベース推定）
        # 過去の案件数から月あたりの自然発生を推定
        organic_new = int(
            self._fc.avg_deal_size_new * self._fc.new_deal_close_rate * 3
        )
        weighted_total = int(weighted + organic_new)

        pipeline_total = sum(o["amount"] for o in opps)
        pipeline_coverage = pipeline_total / self._fc.monthly_target_min if self._fc.monthly_target_min else 0

        # パイプラインカバレッジ判定
        if pipeline_coverage >= 1.5:
            status = "green"
            status_emoji = "🟢"
        elif pipeline_coverage >= 1.0:
            status = "yellow"
            status_emoji = "🟡"
        else:
            status = "red"
            status_emoji = "🔴"

        return {
            "month": month_start,
            "pipeline_total": pipeline_total,
            "weighted": weighted_total,
            "pipeline_coverage": round(pipeline_coverage * 100, 1),
            "status": status,
            "status_emoji": status_emoji,
            "deal_count": len(opps),
            "confirmed": 0,
            "optimistic": int(weighted_total * self._fc.optimistic_multiplier),
            "pessimistic": int(weighted_total * self._fc.pessimistic_multiplier),
            "gap_min": max(0, self._fc.monthly_target_min - weighted_total),
            "gap_max": max(0, self._fc.monthly_target_max - weighted_total),
            "new_count": sum(1 for o in opps if o["deal_type"] == DealType.NEW),
            "existing_count": sum(1 for o in opps if o["deal_type"] == DealType.EXISTING),
        }

    # ------------------------------------------------------------------
    # 逆算ロジック
    # ------------------------------------------------------------------
    def _reverse_calculation(self, gap: int, biz_days_remaining: int) -> dict[str, Any]:
        """目標ギャップから必要アクション数を逆算.

        gap / (close_rate × avg_deal_size) = deals_needed
        → appointments_needed (÷0.5)
        → calls_needed (÷0.05)
        → daily calls (÷ remaining biz days)
        """
        close_rate = self._fc.new_deal_close_rate
        avg_size = self._fc.avg_deal_size_new

        if gap <= 0:
            return {
                "gap": 0,
                "deals_needed": 0,
                "appointments_needed": 0,
                "calls_needed": 0,
                "daily_calls": 0,
            }

        effective_value = close_rate * avg_size
        deals_needed = int(gap / effective_value) + 1 if effective_value > 0 else 0
        appointments_needed = int(deals_needed / 0.5) + 1  # アポ→商談転換率 50%
        calls_needed = int(appointments_needed / 0.05) + 1  # 架電→アポ転換率 5%
        daily_calls = int(calls_needed / biz_days_remaining) + 1 if biz_days_remaining > 0 else calls_needed

        return {
            "gap": gap,
            "deals_needed": deals_needed,
            "appointments_needed": appointments_needed,
            "calls_needed": calls_needed,
            "daily_calls": daily_calls,
        }
