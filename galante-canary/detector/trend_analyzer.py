"""Trend analysis — quarter-over-quarter score comparison."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from storage.score_history import get_score_history

logger = logging.getLogger(__name__)


def analyze_trend(account_id: str, current_score: int) -> dict[str, Any]:
    """Analyze score trend for an account.

    Returns:
        {
            "trend": "improving" | "stable" | "worsening" | "new",
            "delta": int,
            "previous_score": int | None,
            "history_count": int,
            "detail": str,
        }
    """
    history = get_score_history(account_id, limit=10)

    if not history:
        return {
            "trend": "new",
            "delta": 0,
            "previous_score": None,
            "history_count": 0,
            "detail": "初回スキャン — 過去データなし",
        }

    previous_score = history[0]["score"]
    delta = current_score - previous_score

    if delta <= -10:
        trend = "improving"
        detail = f"改善傾向: {previous_score} → {current_score} ({delta:+d})"
    elif delta >= 10:
        trend = "worsening"
        detail = f"悪化傾向: {previous_score} → {current_score} ({delta:+d})"
    else:
        trend = "stable"
        detail = f"安定: {previous_score} → {current_score} ({delta:+d})"

    return {
        "trend": trend,
        "delta": delta,
        "previous_score": previous_score,
        "history_count": len(history),
        "detail": detail,
    }


def analyze_trends(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add trend info to each scored result."""
    enriched: list[dict[str, Any]] = []
    for r in results:
        trend = analyze_trend(r["account_id"], r["score"])
        enriched.append({**r, "trend": trend})
    return enriched


def get_quarter_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Produce a quarter-over-quarter summary.

    Returns counts and averages for current vs. previous quarter.
    """
    now = datetime.now(timezone.utc)
    q_start = now - timedelta(days=90)

    worsening = [r for r in results if r.get("trend", {}).get("trend") == "worsening"]
    improving = [r for r in results if r.get("trend", {}).get("trend") == "improving"]

    avg_score = (
        sum(r["score"] for r in results) / len(results)
        if results
        else 0
    )

    return {
        "total_accounts": len(results),
        "average_score": round(avg_score, 1),
        "worsening_count": len(worsening),
        "improving_count": len(improving),
        "quarter_start": q_start.strftime("%Y-%m-%d"),
        "analysis_date": now.strftime("%Y-%m-%d"),
    }
