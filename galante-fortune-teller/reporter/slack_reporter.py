"""Slack レポーター — WebhookClient でメッセージ投稿."""

from __future__ import annotations

import json
import logging
from typing import Any

from config import AppConfig

logger = logging.getLogger(__name__)


class SlackReporter:
    """Slack Webhook でフォーマット済みメッセージを投稿."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._webhook_url = config.slack.webhook_url

    def post(self, message: str) -> bool:
        """メッセージを Slack に投稿する.

        DRY_RUN の場合はコンソールに出力して True を返す。
        """
        if self._config.dry_run:
            logger.info("=== DRY RUN — Slack メッセージ ===")
            print(message)
            print("=== END ===")
            return True

        if not self._webhook_url:
            logger.error("SLACK_WEBHOOK_URL が未設定です")
            return False

        return self._send_webhook(message)

    def _send_webhook(self, message: str) -> bool:
        """slack_sdk WebhookClient で送信."""
        try:
            from slack_sdk.webhook import WebhookClient  # noqa: WPS433

            client = WebhookClient(self._webhook_url)
            response = client.send(text=message)

            if response.status_code == 200:
                logger.info("Slack 送信成功")
                return True
            else:
                logger.error("Slack 送信失敗: status=%d body=%s", response.status_code, response.body)
                return False
        except ImportError:
            logger.warning("slack_sdk がインストールされていません。urllib で送信を試みます")
            return self._send_urllib(message)
        except Exception as exc:
            logger.error("Slack 送信エラー: %s", exc)
            return False

    def _send_urllib(self, message: str) -> bool:
        """フォールバック: urllib で送信."""
        import urllib.request
        import urllib.error

        payload = json.dumps({"text": message}, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self._webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    logger.info("Slack 送信成功 (urllib)")
                    return True
                logger.error("Slack 返却ステータス: %d", resp.status)
                return False
        except urllib.error.URLError as exc:
            logger.error("Slack 送信失敗 (urllib): %s", exc)
            return False
