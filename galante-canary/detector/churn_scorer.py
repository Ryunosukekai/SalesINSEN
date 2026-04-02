"""Main scoring engine — compute a 0-100 churn risk score per account."""
from __future__ import annotations

import logging
from typing import Any

from config import score_label
from detector.signal_detector import detect_signals

logger = logging.getLogger(__name__)


def score_account(
    account: dict[str, Any],
    account_data: dict[str, Any],
) -> dict[str, Any]:
    """Score a single account and return a result dict.

    Returns:
        {
            "account_id": str,
            "account_name": str,
            "owner_name": str,
            "score": int,          # 0-100
            "label": str,          # e.g. "危険"
            "emoji": str,          # e.g. "🔴"
            "signals": list[dict],
            "signal_summary": str,
        }
    """
    signals = detect_signals(account, account_data)

    # Sum weights, cap at 100
    raw_score = sum(s["weight"] for s in signals)
    score = min(raw_score, 100)

    label_info = score_label(score)

    # Build human-readable signal summary
    signal_summary = " / ".join(s["description"] for s in signals) if signals else "シグナルなし"

    owner = account.get("Owner", {})
    owner_name = owner.get("Name", "不明") if isinstance(owner, dict) else str(owner)

    return {
        "account_id": account.get("Id", ""),
        "account_name": account.get("Name", "不明"),
        "owner_name": owner_name,
        "score": score,
        "label": label_info["label"],
        "emoji": label_info["emoji"],
        "signals": signals,
        "signal_summary": signal_summary,
    }


def score_accounts(
    accounts: list[dict[str, Any]],
    accounts_data: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Score multiple accounts and return sorted results (highest risk first)."""
    results: list[dict[str, Any]] = []
    for acct in accounts:
        acct_id = acct.get("Id", "")
        data = accounts_data.get(acct_id, {})
        result = score_account(acct, data)
        results.append(result)
        logger.info(
            "  %s %s — スコア: %d/100 (%s)",
            result["emoji"],
            result["account_name"],
            result["score"],
            result["label"],
        )
    results.sort(key=lambda r: r["score"], reverse=True)
    return results
