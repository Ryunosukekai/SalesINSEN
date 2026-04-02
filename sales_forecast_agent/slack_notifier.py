"""Slack notification formatter and sender."""

import json
import logging
import urllib.request
import urllib.error
from datetime import date

from .config import AgentConfig
from .models import (
    DangerSignal,
    ForecastReport,
    MonthlyForecast,
    RiskLevel,
)

logger = logging.getLogger(__name__)

# Japanese month format
_MONTH_FMT = "{0}年{1}月"


class SlackNotifier:
    """Formats forecast reports and posts to Slack via webhook."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.slack = config.slack

    def send_report(self, report: ForecastReport) -> bool:
        """Format and send the forecast report to Slack."""
        blocks = self._build_blocks(report)
        payload = {
            "channel": self.slack.channel,
            "username": self.slack.bot_name,
            "icon_emoji": self.slack.bot_emoji,
            "blocks": blocks,
        }

        if self.config.dry_run:
            logger.info("DRY RUN - Slack payload:\n%s", json.dumps(payload, ensure_ascii=False, indent=2))
            return True

        return self._post_webhook(payload)

    def _build_blocks(self, report: ForecastReport) -> list[dict]:
        """Build Slack Block Kit message."""
        blocks = []

        # Header
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":crystal_ball: 商談パイプライン予測レポート",
            },
        })

        # Generated timestamp
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":clock8: {report.generated_at.strftime('%Y/%m/%d %H:%M')} 時点 | "
                    f"パイプライン全体: *{report.total_pipeline_value:,.0f}万円* | "
                    f"案件数: *{report.total_open_deals}件* | "
                    f"平均案件年齢: *{report.avg_deal_age_days:.0f}日*",
                }
            ],
        })

        blocks.append({"type": "divider"})

        # ── Current month forecast ──
        blocks.append(self._month_section(
            report.current_month, ":dart: 今月の着地予測"
        ))

        blocks.append({"type": "divider"})

        # ── Next month danger signals ──
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":warning: *来月の危険信号*",
            },
        })

        next_month_signals = [
            s for s in report.danger_signals
            if _same_month(s.opportunity.close_date, report.next_month.month)
        ]
        if next_month_signals:
            for signal in next_month_signals[:8]:  # Limit to 8
                blocks.append(self._danger_signal_block(signal))
        else:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":white_check_mark: 来月の危険信号はありません",
                },
            })

        # Also show current month danger signals if any
        current_month_signals = [
            s for s in report.danger_signals
            if _same_month(s.opportunity.close_date, report.current_month.month)
        ]
        if current_month_signals:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":rotating_light: *今月の危険信号*",
                },
            })
            for signal in current_month_signals[:8]:
                blocks.append(self._danger_signal_block(signal))

        blocks.append({"type": "divider"})

        # ── 3-month outlook ──
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":chart_with_upwards_trend: *3ヶ月予測サマリー*",
            },
        })

        outlook_lines = []
        for mf in report.three_month_forecasts:
            month_label = _MONTH_FMT.format(mf.month.year, mf.month.month)
            bar = _progress_bar(mf.attainment_pct)
            status = ":red_circle:" if mf.is_at_risk else ":large_green_circle:"
            outlook_lines.append(
                f"{status} *{month_label}*: {mf.weighted_forecast:,.0f}万円 / {mf.target:,.0f}万円 "
                f"({mf.attainment_pct:.1f}%) {bar}"
            )

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(outlook_lines),
            },
        })

        # ── Valley alert ──
        if report.valley_month and report.valley_month.is_at_risk:
            valley_label = _MONTH_FMT.format(
                report.valley_month.month.year, report.valley_month.month.month
            )
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f":hole: *売上谷アラート: {valley_label}*\n"
                        f"加重予測: *{report.valley_month.weighted_forecast:,.0f}万円* "
                        f"(目標比 {report.valley_month.attainment_pct:.1f}%)\n"
                        f"目標とのギャップ: *{report.valley_month.gap_to_target:,.0f}万円*\n"
                        f":arrow_right: あと *{report.valley_month.deals_needed_to_fill_gap}件* "
                        f"の商談を積めば目標に到達"
                    ),
                },
            })

        # ── Gap analysis footer ──
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        f":abacus: 基線レート — 新規成約率: *{self.config.forecast.new_deal_win_rate*100:.1f}%* | "
                        f"既存継続率: *{self.config.forecast.existing_retention_rate*100:.1f}%* | "
                        f"月次目標: *{self.config.forecast.monthly_target:,.0f}万円*"
                    ),
                }
            ],
        })

        return blocks

    def _month_section(self, mf: MonthlyForecast, title: str) -> dict:
        """Build a section block for a monthly forecast."""
        month_label = _MONTH_FMT.format(mf.month.year, mf.month.month)
        bar = _progress_bar(mf.attainment_pct)
        status_emoji = ":tada:" if mf.attainment_pct >= 100 else (
            ":warning:" if mf.is_at_risk else ":muscle:"
        )

        gap_text = ""
        if mf.gap_to_target > 0:
            gap_text = (
                f"\n:arrow_right: ギャップ: *{mf.gap_to_target:,.0f}万円* → "
                f"あと *{mf.deals_needed_to_fill_gap}件* の商談が必要"
            )
        elif mf.gap_to_target <= 0:
            gap_text = "\n:white_check_mark: 目標達成見込み!"

        text = (
            f"*{title}* ({month_label})\n"
            f"{bar} *{mf.attainment_pct:.1f}%* {status_emoji}\n"
            f"\n"
            f":moneybag: パイプライン合計: *{mf.pipeline_total:,.0f}万円*\n"
            f":dart: 加重予測: *{mf.weighted_forecast:,.0f}万円* / 目標 {mf.target:,.0f}万円\n"
            f":handshake: コミット済(85%以上): *{mf.committed_amount:,.0f}万円*\n"
            f":star: ベストケース(50%以上): *{mf.best_case_amount:,.0f}万円*\n"
            f":new: 新規: {mf.new_deal_count}件 | :repeat: 既存: {mf.existing_deal_count}件"
            f"{gap_text}"
        )

        return {
            "type": "section",
            "text": {"type": "mrkdwn", "text": text},
        }

    def _danger_signal_block(self, signal: DangerSignal) -> dict:
        """Build a context block for a danger signal."""
        risk_emoji = {
            RiskLevel.HIGH: ":red_circle:",
            RiskLevel.MEDIUM: ":large_orange_circle:",
            RiskLevel.LOW: ":large_yellow_circle:",
        }
        emoji = risk_emoji.get(signal.risk_level, ":white_circle:")
        return {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        f"{emoji} *{signal.opportunity.name}* "
                        f"({signal.opportunity.account_name} / {signal.opportunity.owner_name}) — "
                        f"{signal.opportunity.amount:,.0f}万円 — "
                        f"{signal.message}"
                    ),
                }
            ],
        }

    def _post_webhook(self, payload: dict) -> bool:
        """Post payload to Slack webhook URL."""
        url = self.slack.webhook_url
        if not url:
            logger.error("SLACK_WEBHOOK_URL is not configured.")
            return False

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    logger.info("Slack message sent successfully.")
                    return True
                logger.error("Slack returned status %d", resp.status)
                return False
        except urllib.error.URLError as e:
            logger.error("Failed to send Slack message: %s", e)
            return False


def _progress_bar(pct: float, width: int = 10) -> str:
    """Generate a text-based progress bar."""
    filled = int(min(pct, 100) / 100 * width)
    empty = width - filled
    return f"`{'█' * filled}{'░' * empty}`"


def _same_month(d: date, month_start: date) -> bool:
    return d.year == month_start.year and d.month == month_start.month
