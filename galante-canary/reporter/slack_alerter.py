"""Slack alert posting via WebhookClient."""
from __future__ import annotations

import logging
from typing import Any

from config import SLACK_WEBHOOK_URL
from reporter.templates import build_daily_alert

logger = logging.getLogger(__name__)


def send_alert(results: list[dict[str, Any]], date_str: str | None = None) -> bool:
    """Post a daily churn alert to Slack.

    Only posts if there are accounts with score >= 40.
    Returns True if the message was sent (or no alert needed), False on error.
    """
    # Check if any account hits the alert threshold
    alertable = [r for r in results if r["score"] >= 40]
    if not alertable:
        logger.info("スコア40以上のアカウントなし — Slack通知スキップ")
        return True

    message = build_daily_alert(results, date_str)

    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL 未設定 — コンソール出力のみ")
        print("\n" + "=" * 60)
        print(message)
        print("=" * 60 + "\n")
        return True

    try:
        from slack_sdk.webhook import WebhookClient  # noqa: WPS433

        client = WebhookClient(url=SLACK_WEBHOOK_URL)
        response = client.send(text=message)

        if response.status_code == 200:
            logger.info("Slack通知を送信しました (アラート対象: %d社)", len(alertable))
            return True
        else:
            logger.error(
                "Slack通知エラー: status=%d body=%s",
                response.status_code,
                response.body,
            )
            return False

    except ImportError:
        logger.warning("slack-sdk 未インストール — コンソール出力のみ")
        print("\n" + "=" * 60)
        print(message)
        print("=" * 60 + "\n")
        return True
    except Exception as exc:
        logger.error("Slack通知の送信に失敗: %s", exc)
        return False
