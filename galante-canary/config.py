"""Galante Canary — 設定ファイル"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "storage" / "canary.db"))
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Salesforce
# ---------------------------------------------------------------------------
SF_USERNAME = os.getenv("SF_USERNAME", "")
SF_PASSWORD = os.getenv("SF_PASSWORD", "")
SF_SECURITY_TOKEN = os.getenv("SF_SECURITY_TOKEN", "")
SF_DOMAIN = os.getenv("SF_DOMAIN", "login")

# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

# ---------------------------------------------------------------------------
# Slack
# ---------------------------------------------------------------------------
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------
SCAN_HOUR = int(os.getenv("SCAN_HOUR", "9"))
SCAN_MINUTE = int(os.getenv("SCAN_MINUTE", "0"))

# ---------------------------------------------------------------------------
# Churn Signals — 11 types
# ---------------------------------------------------------------------------
CHURN_SIGNALS: dict[str, dict] = {
    "no_contact_30d": {
        "description": "30日以上接触なし",
        "weight": 15,
        "severity": "medium",
    },
    "no_contact_60d": {
        "description": "60日以上接触なし",
        "weight": 30,
        "severity": "high",
    },
    "no_contact_90d": {
        "description": "90日以上接触なし",
        "weight": 50,
        "severity": "critical",
    },
    "revenue_decline_20": {
        "description": "前回比で発注額20%以上減少",
        "weight": 20,
        "severity": "medium",
    },
    "revenue_decline_50": {
        "description": "前回比で発注額50%以上減少",
        "weight": 35,
        "severity": "high",
    },
    "longer_cycle": {
        "description": "案件間隔が前回より50%以上延長",
        "weight": 15,
        "severity": "medium",
    },
    "no_pipeline": {
        "description": "常連クライアントに進行中案件ゼロ",
        "weight": 25,
        "severity": "high",
    },
    "meeting_decline": {
        "description": "MTG頻度が前期比で減少",
        "weight": 10,
        "severity": "low",
    },
    "email_no_reply": {
        "description": "直近3通のメールに返信なし",
        "weight": 20,
        "severity": "medium",
    },
    "recent_loss": {
        "description": "直近の提案が失注",
        "weight": 25,
        "severity": "high",
    },
    "consecutive_losses": {
        "description": "連続2回以上失注",
        "weight": 40,
        "severity": "critical",
    },
}

# ---------------------------------------------------------------------------
# Score Ranges
# ---------------------------------------------------------------------------
SCORE_RANGES: list[dict] = [
    {"min": 0, "max": 20, "label": "健全", "emoji": "\U0001f7e2"},
    {"min": 21, "max": 40, "label": "注意", "emoji": "\U0001f7e1"},
    {"min": 41, "max": 60, "label": "警戒", "emoji": "\U0001f7e0"},
    {"min": 61, "max": 80, "label": "危険", "emoji": "\U0001f534"},
    {"min": 81, "max": 100, "label": "緊急", "emoji": "\U0001f6a8"},
]


def score_label(score: int) -> dict:
    """Return the range dict matching *score*."""
    for r in SCORE_RANGES:
        if r["min"] <= score <= r["max"]:
            return r
    return SCORE_RANGES[-1]
