"""Galante Fortune Teller — 全設定."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path

from dotenv import load_dotenv

# .env をプロジェクトルートから読み込む
_PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(_PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# ベースライン指標
# ---------------------------------------------------------------------------
BASELINE_METRICS: dict = {
    "monthly_revenue_target_min": 25_000_000,   # 2,500万円
    "monthly_revenue_target_max": 33_000_000,   # 3,300万円
    "annual_target_min": 300_000_000,
    "annual_target_max": 400_000_000,
    "new_deal_close_rate": 0.104,
    "existing_deal_continue_rate": 0.229,
    "average_deal_size_new": 1_500_000,
    "average_deal_size_existing": 3_000_000,
    "sales_cycle_days_new": 30,
    "sales_cycle_days_existing": 14,
}

# ステージ別確率マッピング
STAGE_PROBABILITIES: dict[str, float] = {
    # English stage names
    "Prospecting": 0.10,
    "Qualification": 0.20,
    "Needs Analysis": 0.35,
    "Value Proposition": 0.50,
    "Id. Decision Makers": 0.60,
    "Perception Analysis": 0.70,
    "Proposal/Price Quote": 0.75,
    "Negotiation/Review": 0.85,
    "Closed Won": 1.00,
    "Closed Lost": 0.00,
    # Japanese stage names
    "リード": 0.10,
    "ヒアリング": 0.20,
    "課題特定": 0.35,
    "提案": 0.50,
    "見積提示": 0.70,
    "最終交渉": 0.85,
    "受注": 1.00,
    "失注": 0.00,
}


# ---------------------------------------------------------------------------
# サブ設定データクラス
# ---------------------------------------------------------------------------
@dataclass
class SalesforceConfig:
    """Salesforce接続設定."""

    username: str = field(default_factory=lambda: os.environ.get("SF_USERNAME", ""))
    password: str = field(default_factory=lambda: os.environ.get("SF_PASSWORD", ""))
    security_token: str = field(default_factory=lambda: os.environ.get("SF_SECURITY_TOKEN", ""))
    domain: str = field(default_factory=lambda: os.environ.get("SF_DOMAIN", "login"))
    api_version: str = field(default_factory=lambda: os.environ.get("SF_API_VERSION", "59.0"))


@dataclass
class SlackConfig:
    """Slack通知設定."""

    webhook_url: str = field(default_factory=lambda: os.environ.get("SLACK_WEBHOOK_URL", ""))
    channel: str = field(default_factory=lambda: os.environ.get("SLACK_CHANNEL", "#sales-forecast"))
    bot_name: str = "Fortune Teller"
    bot_emoji: str = ":crystal_ball:"


@dataclass
class ForecastConfig:
    """予測計算パラメータ."""

    monthly_target_min: int = BASELINE_METRICS["monthly_revenue_target_min"]
    monthly_target_max: int = BASELINE_METRICS["monthly_revenue_target_max"]
    annual_target_min: int = BASELINE_METRICS["annual_target_min"]
    annual_target_max: int = BASELINE_METRICS["annual_target_max"]
    new_deal_close_rate: float = BASELINE_METRICS["new_deal_close_rate"]
    existing_deal_continue_rate: float = BASELINE_METRICS["existing_deal_continue_rate"]
    avg_deal_size_new: int = BASELINE_METRICS["average_deal_size_new"]
    avg_deal_size_existing: int = BASELINE_METRICS["average_deal_size_existing"]
    sales_cycle_days_new: int = BASELINE_METRICS["sales_cycle_days_new"]
    sales_cycle_days_existing: int = BASELINE_METRICS["sales_cycle_days_existing"]

    stage_probabilities: dict[str, float] = field(default_factory=lambda: dict(STAGE_PROBABILITIES))

    # 危険信号しきい値
    stale_days_threshold: int = 14
    close_date_slip_threshold: int = 2
    forecast_months: int = 3

    # 月末ラッシュ補正係数 (残5営業日以内で +5%)
    month_end_rush_factor: float = 0.05
    # 楽観/悲観レンジ
    optimistic_multiplier: float = 1.20
    pessimistic_multiplier: float = 0.75


@dataclass
class SchedulerConfig:
    """スケジューラ設定."""

    daily_run_time: time = field(
        default_factory=lambda: time(
            hour=int(os.environ.get("DAILY_RUN_HOUR", "8")),
            minute=int(os.environ.get("DAILY_RUN_MINUTE", "30")),
        )
    )
    weekly_run_time: time = field(default_factory=lambda: time(hour=8, minute=0))
    monthly_run_time: time = field(default_factory=lambda: time(hour=8, minute=0))
    timezone: str = field(default_factory=lambda: os.environ.get("TZ", "Asia/Tokyo"))


@dataclass
class AppConfig:
    """ルート設定."""

    salesforce: SalesforceConfig = field(default_factory=SalesforceConfig)
    slack: SlackConfig = field(default_factory=SlackConfig)
    forecast: ForecastConfig = field(default_factory=ForecastConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    anthropic_api_key: str = field(
        default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", "")
    )
    dry_run: bool = field(
        default_factory=lambda: os.environ.get("DRY_RUN", "false").lower() == "true"
    )
    log_level: str = field(default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO"))
    db_path: str = field(
        default_factory=lambda: str(_PROJECT_ROOT / "storage" / "forecast_history.db")
    )
