"""Slack メッセージテンプレート（日次・週次・月次）."""

from __future__ import annotations

from datetime import date
from typing import Any


def _yen(amount: int) -> str:
    """円表示フォーマット."""
    return f"¥{amount:,}"


def _month_label(d: date) -> str:
    return f"{d.year}年{d.month}月"


def _progress_bar(pct: float, width: int = 10) -> str:
    filled = int(min(pct, 100) / 100 * width)
    empty = width - filled
    return f"`{'█' * filled}{'░' * empty}`"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 日次テンプレート
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class DailyTemplate:
    """日次レポートテンプレート."""

    @staticmethod
    def render(
        forecast: dict[str, Any],
        alerts: list[dict[str, Any]],
        ai_advice: str,
    ) -> str:
        current = forecast["current_month"]
        reverse = forecast["reverse"]
        three_month = forecast["three_month"]
        today = forecast["date"]
        biz_days = forecast["biz_days_remaining"]

        lines: list[str] = []

        # ヘッダー
        lines.append("🔮 *Galante Fortune Teller — 本日の売上予測*")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        lines.append(f"📅 {today.strftime('%Y/%m/%d')} | 残営業日: {biz_days}日")
        lines.append("")

        # 今月の着地予測
        lines.append("*【今月の着地予測】*")
        lines.append(f"├ 確定売上:     {_yen(current['confirmed'])}")
        lines.append(f"├ 加重予測:     {_yen(current['weighted'])}（パイプライン × 成約確率）")
        lines.append(f"├ 楽観予測:     {_yen(current['optimistic'])}")
        lines.append(f"├ 悲観予測:     {_yen(current['pessimistic'])}")
        lines.append("│")
        lines.append(f"├ 🎯 ミニマム目標（¥25,000,000）との差: ▲{_yen(current['gap_min'])}")
        lines.append(f"└ 🏆 チャレンジ目標（¥33,000,000）との差: ▲{_yen(current['gap_max'])}")
        lines.append("")

        # 目標達成に必要なアクション
        lines.append("*【目標達成に必要なアクション】*")
        lines.append(f"├ 追加必要商談数: {reverse['deals_needed']}件（成約率10.4%ベース）")
        lines.append(f"├ 必要アポ数:     {reverse['appointments_needed']}件")
        lines.append(f"└ 日次必要架電数: {reverse['daily_calls']}件/日")
        lines.append("")

        # 来月以降の先行指標
        lines.append("*【来月以降の先行指標】*")
        for m in three_month:
            label = _month_label(m["month"])
            emoji = m.get("status_emoji", "⚪")
            coverage = m.get("pipeline_coverage", "")
            coverage_str = f"（カバレッジ {coverage}%）" if coverage else ""
            lines.append(f"  {emoji} {label}: 加重 {_yen(m['weighted'])} / パイプライン {_yen(m['pipeline_total'])}{coverage_str}")
        lines.append("")

        # アラート
        lines.append("*【⚠️ 今日のアラート】*")
        if alerts:
            for a in alerts[:8]:
                severity_icon = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟡"}.get(a["severity"], "⚪")
                lines.append(
                    f"  {severity_icon} *{a['opp_name']}*"
                    f"（{a['account_name']} / {a['owner_name']}）"
                    f"— {_yen(a['amount'])} — {a['message']}"
                )
        else:
            lines.append("  ✅ アラートなし")
        lines.append("")

        # AIアドバイス
        lines.append("*【🤖 AIアドバイス】*")
        for line in ai_advice.strip().split("\n"):
            lines.append(f"  {line}")
        lines.append("")
        lines.append("_Powered by Galante Fortune Teller 🔮_")

        return "\n".join(lines)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 週次テンプレート
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class WeeklyTemplate:
    """月曜朝の週次サマリーテンプレート."""

    @staticmethod
    def render(
        forecast: dict[str, Any],
        alerts: list[dict[str, Any]],
        ai_advice: str,
        weekly_won: list[dict[str, Any]] | None = None,
        weekly_lost: list[dict[str, Any]] | None = None,
        close_rate_trend: list[float] | None = None,
        pipeline_history: list[dict[str, Any]] | None = None,
    ) -> str:
        weekly_won = weekly_won or []
        weekly_lost = weekly_lost or []
        close_rate_trend = close_rate_trend or []
        pipeline_history = pipeline_history or []

        current = forecast["current_month"]
        today = forecast["date"]
        biz_days = forecast["biz_days_remaining"]

        lines: list[str] = []

        lines.append("🔮 *Galante Fortune Teller — 週次サマリー*")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        lines.append(f"📅 {today.strftime('%Y/%m/%d')}（月曜） | 残営業日: {biz_days}日")
        lines.append("")

        # 先週の受注/失注
        lines.append("*【先週の受注・失注】*")
        won_total = sum(o["amount"] for o in weekly_won)
        lost_total = sum(o["amount"] for o in weekly_lost)
        lines.append(f"  🏆 受注: {len(weekly_won)}件 / {_yen(won_total)}")
        for w in weekly_won[:5]:
            lines.append(f"    └ {w['name']} ({_yen(w['amount'])})")
        lines.append(f"  ❌ 失注: {len(weekly_lost)}件 / {_yen(lost_total)}")
        for lo in weekly_lost[:5]:
            lines.append(f"    └ {lo['name']} ({_yen(lo['amount'])})")
        lines.append("")

        # 成約率トレンド（4週移動平均）
        if close_rate_trend:
            lines.append("*【成約率トレンド（4週移動平均）】*")
            for i, rate in enumerate(close_rate_trend):
                week_label = f"W-{len(close_rate_trend) - i}"
                bar_len = int(rate * 50)
                lines.append(f"  {week_label}: {'▓' * bar_len}{'░' * (50 - bar_len)} {rate*100:.1f}%")
            lines.append("")

        # パイプライン推移（ASCII グラフ）
        if pipeline_history:
            lines.append("*【パイプライン推移】*")
            max_val = max((h.get("pipeline_total", 0) for h in pipeline_history), default=1) or 1
            for h in pipeline_history[-8:]:
                d = h.get("date", "")
                val = h.get("pipeline_total", 0)
                bar_len = int(val / max_val * 30)
                lines.append(f"  {d}: {'█' * bar_len} {_yen(val)}")
            lines.append("")

        # 日次テンプレートと同じ着地予測・アラート・AIアドバイス
        lines.append("*【今月の着地予測】*")
        lines.append(f"  確定: {_yen(current['confirmed'])} | 加重: {_yen(current['weighted'])} | 楽観: {_yen(current['optimistic'])} | 悲観: {_yen(current['pessimistic'])}")
        lines.append(f"  🎯 ミニマム差: ▲{_yen(current['gap_min'])} | 🏆 チャレンジ差: ▲{_yen(current['gap_max'])}")
        lines.append("")

        # 来月以降
        lines.append("*【来月以降の先行指標】*")
        for m in forecast["three_month"]:
            label = _month_label(m["month"])
            emoji = m.get("status_emoji", "⚪")
            lines.append(f"  {emoji} {label}: 加重 {_yen(m['weighted'])} / パイプライン {_yen(m['pipeline_total'])}")
        lines.append("")

        # アラート
        lines.append("*【⚠️ アラート】*")
        if alerts:
            for a in alerts[:10]:
                icon = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟡"}.get(a["severity"], "⚪")
                lines.append(f"  {icon} {a['opp_name']} — {a['message']}")
        else:
            lines.append("  ✅ アラートなし")
        lines.append("")

        lines.append("*【🤖 AIアドバイス】*")
        for line in ai_advice.strip().split("\n"):
            lines.append(f"  {line}")
        lines.append("")
        lines.append("_Powered by Galante Fortune Teller 🔮_")

        return "\n".join(lines)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 月次テンプレート
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class MonthlyTemplate:
    """月初の月次レポートテンプレート."""

    @staticmethod
    def render(
        forecast: dict[str, Any],
        alerts: list[dict[str, Any]],
        ai_advice: str,
        pipeline_summary: dict[str, Any] | None = None,
        monthly_history: list[dict[str, Any]] | None = None,
    ) -> str:
        pipeline_summary = pipeline_summary or {}
        monthly_history = monthly_history or []
        current = forecast["current_month"]
        today = forecast["date"]

        lines: list[str] = []

        lines.append("🔮 *Galante Fortune Teller — 月次レポート*")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        lines.append(f"📅 {today.strftime('%Y/%m/%d')} | {_month_label(today)}度")
        lines.append("")

        # 前月実績振り返り
        if monthly_history:
            last = monthly_history[-1]
            lines.append("*【前月実績】*")
            lines.append(f"  売上実績: {_yen(last.get('actual_revenue', 0))}")
            lines.append(f"  予測精度: {last.get('forecast_accuracy', 0):.1f}%")
            lines.append("")

        # パイプライン概況
        lines.append("*【パイプライン概況】*")
        lines.append(f"  総パイプライン: {_yen(pipeline_summary.get('total_pipeline', 0))}")
        lines.append(f"  案件数: {pipeline_summary.get('total_deals', 0)}件")
        lines.append(f"  新規: {pipeline_summary.get('new_deal_count', 0)}件 ({_yen(pipeline_summary.get('new_deal_amount', 0))})")
        lines.append(f"  既存: {pipeline_summary.get('existing_deal_count', 0)}件 ({_yen(pipeline_summary.get('existing_deal_amount', 0))})")
        lines.append(f"  平均案件サイズ: {_yen(pipeline_summary.get('avg_deal_size', 0))}")
        lines.append(f"  平均案件年齢: {pipeline_summary.get('avg_age_days', 0)}日")
        lines.append("")

        # ステージ別内訳
        stage_summary = pipeline_summary.get("stage_summary", {})
        if stage_summary:
            lines.append("*【ステージ別内訳】*")
            for stage, data in sorted(stage_summary.items(), key=lambda x: -x[1]["amount"]):
                lines.append(f"  {stage}: {data['count']}件 / {_yen(data['amount'])}")
            lines.append("")

        # 担当者別
        owner_summary = pipeline_summary.get("owner_summary", {})
        if owner_summary:
            lines.append("*【担当者別】*")
            for owner, data in sorted(owner_summary.items(), key=lambda x: -x[1]["amount"]):
                lines.append(f"  {owner}: {data['count']}件 / {_yen(data['amount'])}")
            lines.append("")

        # 3ヶ月予測
        lines.append("*【3ヶ月予測】*")
        for m in forecast["three_month"]:
            label = _month_label(m["month"])
            emoji = m.get("status_emoji", "⚪")
            pct = m.get("pipeline_coverage", 0)
            lines.append(f"  {emoji} {label}: 加重 {_yen(m['weighted'])} / パイプライン {_yen(m['pipeline_total'])}")
        lines.append("")

        # 年間進捗
        lines.append("*【年間進捗】*")
        lines.append(f"  ミニマム目標: ¥300,000,000 | チャレンジ目標: ¥400,000,000")
        if monthly_history:
            ytd = sum(h.get("actual_revenue", 0) for h in monthly_history)
            lines.append(f"  YTD実績: {_yen(ytd)}")
            lines.append(f"  ミニマム達成率: {ytd / 300_000_000 * 100:.1f}%")
        lines.append("")

        # アラート
        lines.append("*【⚠️ アラート】*")
        if alerts:
            for a in alerts[:10]:
                icon = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟡"}.get(a["severity"], "⚪")
                lines.append(f"  {icon} {a['opp_name']} — {a['message']}")
        else:
            lines.append("  ✅ アラートなし")
        lines.append("")

        lines.append("*【🤖 AIアドバイス】*")
        for line in ai_advice.strip().split("\n"):
            lines.append(f"  {line}")
        lines.append("")
        lines.append("_Powered by Galante Fortune Teller 🔮_")

        return "\n".join(lines)
