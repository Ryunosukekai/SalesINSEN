"""Core forecast calculation engine."""

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from .config import AgentConfig
from .models import (
    DangerSignal,
    DealType,
    ForecastReport,
    MonthlyForecast,
    Opportunity,
    RiskLevel,
)

logger = logging.getLogger(__name__)


class ForecastEngine:
    """Calculates sales forecasts and identifies danger signals."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.fc = config.forecast

    def generate_report(self, opportunities: list[Opportunity]) -> ForecastReport:
        """Generate a complete forecast report from opportunity data."""
        today = date.today()

        # Build monthly forecasts for current + next N months
        monthly_forecasts = []
        for offset in range(self.fc.forecast_months):
            month_start = _first_of_month(today, offset)
            month_opps = [
                o for o in opportunities if _same_month(o.close_date, month_start)
            ]
            forecast = self._calculate_monthly_forecast(month_start, month_opps)
            monthly_forecasts.append(forecast)

        current_month = monthly_forecasts[0]
        next_month = monthly_forecasts[1] if len(monthly_forecasts) > 1 else current_month

        # Identify the valley (lowest weighted forecast)
        valley = min(monthly_forecasts, key=lambda f: f.weighted_forecast)

        # Detect danger signals
        danger_signals = self._detect_danger_signals(opportunities)

        # Summary metrics
        total_pipeline = sum(o.amount for o in opportunities)
        avg_age = 0.0
        if opportunities:
            avg_age = sum(
                (today - o.created_date).days for o in opportunities
            ) / len(opportunities)

        return ForecastReport(
            generated_at=datetime.now(),
            current_month=current_month,
            next_month=next_month,
            three_month_forecasts=monthly_forecasts,
            danger_signals=danger_signals,
            valley_month=valley,
            total_pipeline_value=total_pipeline,
            total_open_deals=len(opportunities),
            avg_deal_age_days=avg_age,
        )

    def _calculate_monthly_forecast(
        self, month_start: date, opportunities: list[Opportunity]
    ) -> MonthlyForecast:
        """Calculate forecast for a single month."""
        pipeline_total = sum(o.amount for o in opportunities)

        # Weighted forecast: apply deal-type-specific win rates
        weighted = 0.0
        for opp in opportunities:
            base_rate = (
                self.fc.existing_retention_rate
                if opp.deal_type == DealType.EXISTING
                else self.fc.new_deal_win_rate
            )
            # Blend Salesforce stage probability with our baseline rate
            blended_prob = (opp.probability + base_rate) / 2.0
            weighted += opp.amount * blended_prob

        committed = sum(o.amount for o in opportunities if o.probability >= 0.85)
        best_case = sum(o.amount for o in opportunities if o.probability >= 0.50)

        new_count = sum(1 for o in opportunities if o.deal_type == DealType.NEW)
        existing_count = sum(1 for o in opportunities if o.deal_type == DealType.EXISTING)

        target = self.fc.monthly_target
        gap = target - weighted

        # Reverse-calculate deals needed to fill gap
        deals_needed = 0
        if gap > 0:
            # Use weighted average of new/existing deal sizes and win rates
            effective_value_per_deal = (
                self.fc.avg_deal_size_new * self.fc.new_deal_win_rate * 0.7
                + self.fc.avg_deal_size_existing * self.fc.existing_retention_rate * 0.3
            )
            if effective_value_per_deal > 0:
                deals_needed = int(gap / effective_value_per_deal) + 1

        return MonthlyForecast(
            month=month_start,
            pipeline_total=pipeline_total,
            weighted_forecast=weighted,
            committed_amount=committed,
            best_case_amount=best_case,
            new_deal_count=new_count,
            existing_deal_count=existing_count,
            target=target,
            gap_to_target=gap,
            deals_needed_to_fill_gap=max(0, deals_needed),
        )

    def _detect_danger_signals(
        self, opportunities: list[Opportunity]
    ) -> list[DangerSignal]:
        """Identify risk factors across all opportunities."""
        signals: list[DangerSignal] = []
        today = date.today()

        for opp in opportunities:
            # 1. Stale deals - no activity for N days
            if opp.days_since_last_activity >= self.fc.stale_days_threshold:
                signals.append(
                    DangerSignal(
                        opportunity=opp,
                        risk_level=RiskLevel.HIGH
                        if opp.days_since_last_activity >= self.fc.stale_days_threshold * 2
                        else RiskLevel.MEDIUM,
                        signal_type="stale",
                        message=f"{opp.days_since_last_activity}日間活動なし",
                    )
                )

            # 2. Close date slipping
            if opp.close_date_change_count >= self.fc.close_date_slip_threshold:
                signals.append(
                    DangerSignal(
                        opportunity=opp,
                        risk_level=RiskLevel.HIGH,
                        signal_type="slipping",
                        message=f"クローズ日が{opp.close_date_change_count}回変更済み",
                    )
                )

            # 3. Overdue close date (past due but still open)
            if opp.close_date < today:
                signals.append(
                    DangerSignal(
                        opportunity=opp,
                        risk_level=RiskLevel.HIGH,
                        signal_type="overdue",
                        message=f"クローズ予定日を{(today - opp.close_date).days}日超過",
                    )
                )

            # 4. Large deal at low stage
            if opp.amount >= self.fc.avg_deal_size_new * 3 and opp.probability < 0.35:
                signals.append(
                    DangerSignal(
                        opportunity=opp,
                        risk_level=RiskLevel.MEDIUM,
                        signal_type="large_early_stage",
                        message=f"大型案件({opp.amount:.0f}万円)がまだ初期段階({opp.stage})",
                    )
                )

            # 5. Close date within 2 weeks but low probability
            days_to_close = (opp.close_date - today).days
            if 0 <= days_to_close <= 14 and opp.probability < 0.50:
                signals.append(
                    DangerSignal(
                        opportunity=opp,
                        risk_level=RiskLevel.HIGH,
                        signal_type="closing_soon_low_prob",
                        message=f"あと{days_to_close}日でクローズ予定だが確度{opp.probability*100:.0f}%",
                    )
                )

        # Sort by risk level (HIGH first) then by deal amount
        risk_order = {RiskLevel.HIGH: 0, RiskLevel.MEDIUM: 1, RiskLevel.LOW: 2}
        signals.sort(key=lambda s: (risk_order[s.risk_level], -s.opportunity.amount))

        return signals


def _first_of_month(base_date: date, month_offset: int) -> date:
    """Get the first day of the month with offset."""
    month = base_date.month + month_offset
    year = base_date.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    return date(year, month, 1)


def _same_month(d: date, month_start: date) -> bool:
    """Check if a date falls within the same month."""
    return d.year == month_start.year and d.month == month_start.month
