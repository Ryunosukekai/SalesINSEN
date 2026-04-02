"""Configuration for the Sales Forecast Agent."""

import os
from dataclasses import dataclass, field
from datetime import time


@dataclass
class SalesforceConfig:
    """Salesforce connection settings."""

    username: str = field(default_factory=lambda: os.environ.get("SF_USERNAME", ""))
    password: str = field(default_factory=lambda: os.environ.get("SF_PASSWORD", ""))
    security_token: str = field(
        default_factory=lambda: os.environ.get("SF_SECURITY_TOKEN", "")
    )
    domain: str = field(
        default_factory=lambda: os.environ.get("SF_DOMAIN", "login")
    )  # 'login' or 'test'
    api_version: str = field(
        default_factory=lambda: os.environ.get("SF_API_VERSION", "59.0")
    )


@dataclass
class SlackConfig:
    """Slack notification settings."""

    webhook_url: str = field(
        default_factory=lambda: os.environ.get("SLACK_WEBHOOK_URL", "")
    )
    channel: str = field(
        default_factory=lambda: os.environ.get("SLACK_CHANNEL", "#sales-forecast")
    )
    bot_name: str = "Fortune Teller"
    bot_emoji: str = ":crystal_ball:"


@dataclass
class ForecastConfig:
    """Forecast calculation parameters."""

    # Baseline conversion rates
    new_deal_win_rate: float = field(
        default_factory=lambda: float(
            os.environ.get("NEW_DEAL_WIN_RATE", "0.104")
        )
    )  # 10.4%
    existing_retention_rate: float = field(
        default_factory=lambda: float(
            os.environ.get("EXISTING_RETENTION_RATE", "0.229")
        )
    )  # 22.9%

    # Monthly sales target (万円)
    monthly_target: float = field(
        default_factory=lambda: float(
            os.environ.get("MONTHLY_SALES_TARGET", "10000")
        )
    )  # 1億円 = 10000万円

    # Average deal size (万円)
    avg_deal_size_new: float = field(
        default_factory=lambda: float(
            os.environ.get("AVG_DEAL_SIZE_NEW", "500")
        )
    )
    avg_deal_size_existing: float = field(
        default_factory=lambda: float(
            os.environ.get("AVG_DEAL_SIZE_EXISTING", "300")
        )
    )

    # Stage-based probability mapping (Salesforce stage name -> probability)
    stage_probabilities: dict = field(default_factory=lambda: {
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
    })

    # Danger signal thresholds
    stale_days_threshold: int = 14  # Days without activity = stale
    close_date_slip_threshold: int = 2  # Number of close date changes = danger

    # Forecast horizon
    forecast_months: int = 3


@dataclass
class SchedulerConfig:
    """Scheduler settings."""

    daily_run_time: time = field(
        default_factory=lambda: time(
            hour=int(os.environ.get("DAILY_RUN_HOUR", "8")),
            minute=int(os.environ.get("DAILY_RUN_MINUTE", "0")),
        )
    )
    timezone: str = field(
        default_factory=lambda: os.environ.get("TZ", "Asia/Tokyo")
    )


@dataclass
class AgentConfig:
    """Root configuration combining all sub-configs."""

    salesforce: SalesforceConfig = field(default_factory=SalesforceConfig)
    slack: SlackConfig = field(default_factory=SlackConfig)
    forecast: ForecastConfig = field(default_factory=ForecastConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    dry_run: bool = field(
        default_factory=lambda: os.environ.get("DRY_RUN", "false").lower() == "true"
    )
    log_level: str = field(
        default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO")
    )
