"""Data models for the Sales Forecast Agent."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class DealType(Enum):
    NEW = "new"
    EXISTING = "existing"


class RiskLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Opportunity:
    """Salesforce Opportunity record."""

    id: str
    name: str
    amount: float  # 万円
    stage: str
    close_date: date
    deal_type: DealType
    owner_name: str
    account_name: str
    probability: float  # 0.0 - 1.0
    created_date: date
    last_activity_date: Optional[date] = None
    days_since_last_activity: int = 0
    close_date_change_count: int = 0
    next_step: Optional[str] = None


@dataclass
class DangerSignal:
    """A risk indicator for a specific opportunity."""

    opportunity: Opportunity
    risk_level: RiskLevel
    signal_type: str  # e.g., "stale", "slipping", "low_probability_large_deal"
    message: str


@dataclass
class MonthlyForecast:
    """Forecast for a single month."""

    month: date  # First day of the month
    pipeline_total: float  # Total pipeline amount (万円)
    weighted_forecast: float  # Probability-weighted amount (万円)
    committed_amount: float  # High-probability (>=85%) deals
    best_case_amount: float  # Medium+ probability (>=50%) deals
    new_deal_count: int
    existing_deal_count: int
    target: float  # Monthly target (万円)
    gap_to_target: float  # target - weighted_forecast
    deals_needed_to_fill_gap: int  # Additional deals needed

    @property
    def attainment_pct(self) -> float:
        if self.target == 0:
            return 0.0
        return (self.weighted_forecast / self.target) * 100

    @property
    def is_at_risk(self) -> bool:
        return self.attainment_pct < 80.0


@dataclass
class ForecastReport:
    """Complete forecast report for Slack posting."""

    generated_at: datetime
    current_month: MonthlyForecast
    next_month: MonthlyForecast
    three_month_forecasts: list  # list[MonthlyForecast]
    danger_signals: list  # list[DangerSignal]
    valley_month: Optional[MonthlyForecast] = None  # Lowest forecast month

    # Summary metrics
    total_pipeline_value: float = 0.0
    total_open_deals: int = 0
    avg_deal_age_days: float = 0.0
