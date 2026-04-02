"""AI コメンテーター — Claude API で経営アドバイスを生成."""

from __future__ import annotations

import logging
import os
from typing import Any

from config import AppConfig

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
あなたはGalanteの経営参謀です。
以下のパイプラインデータを分析し、代表の甲斐龍之介に向けて
「今日やるべきこと」を3つ以内で具体的に提案してください。

トーンは格調高くも率直に。「紳士的だが甘くない」スタイルで。
数字に基づいた提案を行い、感覚論は排除してください。

回答は以下の形式で出力してください（番号付きリスト、各項目2行以内）:
1. [アクション]: [理由・根拠]
2. [アクション]: [理由・根拠]
3. [アクション]: [理由・根拠]
"""


class AICommentator:
    """Claude API を使ったAIアドバイザー."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._api_key = config.anthropic_api_key

    def generate_advice(
        self,
        pipeline_summary: dict[str, Any],
        forecast: dict[str, Any],
        alerts: list[dict[str, Any]],
    ) -> str:
        """パイプラインデータからCEO向けアクションアイテムを生成.

        ANTHROPIC_API_KEY が未設定の場合はフォールバックメッセージを返す。
        """
        if not self._api_key:
            logger.info("ANTHROPIC_API_KEY が未設定のため、AIアドバイスをスキップします")
            return self._fallback_advice(forecast, alerts)

        try:
            return self._call_claude(pipeline_summary, forecast, alerts)
        except Exception as exc:
            logger.warning("Claude API 呼び出しに失敗: %s", exc)
            return self._fallback_advice(forecast, alerts)

    def _call_claude(
        self,
        summary: dict[str, Any],
        forecast: dict[str, Any],
        alerts: list[dict[str, Any]],
    ) -> str:
        """Claude API を呼び出す（lazy import）."""
        import anthropic  # noqa: WPS433

        client = anthropic.Anthropic(api_key=self._api_key)

        # データをテキスト化
        user_message = self._build_data_prompt(summary, forecast, alerts)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        content = message.content[0].text if message.content else ""
        logger.info("Claude AI アドバイス生成完了")
        return content.strip()

    @staticmethod
    def _build_data_prompt(
        summary: dict[str, Any],
        forecast: dict[str, Any],
        alerts: list[dict[str, Any]],
    ) -> str:
        """Claude に渡すデータプロンプトを構築."""
        current = forecast.get("current_month", {})
        reverse = forecast.get("reverse", {})

        lines = [
            "## 本日のパイプラインデータ",
            f"- 日付: {forecast.get('date', '不明')}",
            f"- 残営業日: {forecast.get('biz_days_remaining', 0)}日",
            f"- 確定売上: ¥{current.get('confirmed', 0):,}",
            f"- 加重予測: ¥{current.get('weighted', 0):,}",
            f"- ミニマム目標との差: ¥{current.get('gap_min', 0):,}",
            f"- チャレンジ目標との差: ¥{current.get('gap_max', 0):,}",
            f"- パイプライン合計: ¥{current.get('pipeline_total', 0):,}",
            f"- 商談数: {current.get('deal_count', 0)}件（新規{current.get('new_count', 0)} / 既存{current.get('existing_count', 0)}）",
            "",
            "## 逆算アクション",
            f"- 追加必要商談数: {reverse.get('deals_needed', 0)}件",
            f"- 必要アポ数: {reverse.get('appointments_needed', 0)}件",
            f"- 日次必要架電数: {reverse.get('daily_calls', 0)}件/日",
            "",
            "## 3ヶ月予測",
        ]

        for m in forecast.get("three_month", []):
            month_label = f"{m['month'].year}年{m['month'].month}月"
            lines.append(f"- {month_label}: 加重¥{m.get('weighted', 0):,} {m.get('status_emoji', '')}")

        if alerts:
            lines.append("")
            lines.append(f"## アラート（{len(alerts)}件）")
            for a in alerts[:10]:
                lines.append(f"- [{a['severity']}] {a['opp_name']}: {a['message']}")

        return "\n".join(lines)

    @staticmethod
    def _fallback_advice(
        forecast: dict[str, Any],
        alerts: list[dict[str, Any]],
    ) -> str:
        """API不使用時のルールベースフォールバック."""
        items: list[str] = []
        current = forecast.get("current_month", {})
        reverse = forecast.get("reverse", {})

        # 1. ギャップに基づくアドバイス
        gap = current.get("gap_min", 0)
        if gap > 0:
            daily = reverse.get("daily_calls", 0)
            items.append(
                f"1. 目標まで¥{gap:,}の不足 — 本日から1日{daily}件の架電を徹底し、"
                "パイプラインを積み上げてください"
            )
        else:
            items.append(
                "1. ミニマム目標は射程圏内 — チャレンジ目標¥33,000,000に向けて"
                "高確度案件のクロージングを優先してください"
            )

        # 2. アラート対応
        high_alerts = [a for a in alerts if a["severity"] == "HIGH"]
        if high_alerts:
            top = high_alerts[0]
            items.append(
                f"2. 最優先対応: 「{top['opp_name']}」({top['message']}) — "
                "本日中にアクションを起こしてください"
            )
        else:
            items.append("2. 重大アラートなし — 新規開拓とヒアリング精度向上に時間を投資してください")

        # 3. パイプライン充実
        items.append(
            "3. 来月以降のパイプラインが目標の150%を下回る月がないか確認し、"
            "不足があれば今週中に種まきを開始してください"
        )

        return "\n".join(items)
