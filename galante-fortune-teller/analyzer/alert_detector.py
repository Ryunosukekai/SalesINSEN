"""危険信号検出エンジン."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from config import AppConfig

logger = logging.getLogger(__name__)

# アラート種別
ALERT_STALE = "stale"
ALERT_SLIPPING = "slipping"
ALERT_OVERDUE = "overdue"
ALERT_LARGE_EARLY = "large_early"
ALERT_CLOSING_SOON_LOW_PROB = "closing_soon_low_prob"


class AlertDetector:
    """パイプライン内の危険信号を検出."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._fc = config.forecast

    def detect(self, opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """全商談をスキャンし、アラート一覧を返す."""
        alerts: list[dict[str, Any]] = []
        today = date.today()

        for opp in opportunities:
            # 1. 停滞案件: N日間活動なし
            days_inactive = opp["days_since_last_activity"]
            if days_inactive >= self._fc.stale_days_threshold:
                severity = "HIGH" if days_inactive >= self._fc.stale_days_threshold * 2 else "MEDIUM"
                alerts.append(self._make_alert(
                    opp=opp,
                    alert_type=ALERT_STALE,
                    severity=severity,
                    message=f"{days_inactive}日間活動なし — フォローが必要です",
                ))

            # 2. クローズ日スリッピング
            if opp["close_date_change_count"] >= self._fc.close_date_slip_threshold:
                alerts.append(self._make_alert(
                    opp=opp,
                    alert_type=ALERT_SLIPPING,
                    severity="HIGH",
                    message=f"クローズ日が{opp['close_date_change_count']}回変更 — 案件コントロールに懸念",
                ))

            # 3. 期限超過（クローズ予定日を過ぎてまだオープン）
            if opp["close_date"] < today:
                overdue_days = (today - opp["close_date"]).days
                alerts.append(self._make_alert(
                    opp=opp,
                    alert_type=ALERT_OVERDUE,
                    severity="HIGH",
                    message=f"クローズ予定日を{overdue_days}日超過 — 即時対応が必要",
                ))

            # 4. 大型案件が初期ステージ
            if opp["amount"] >= self._fc.avg_deal_size_new * 3 and opp["probability"] < 0.35:
                alerts.append(self._make_alert(
                    opp=opp,
                    alert_type=ALERT_LARGE_EARLY,
                    severity="MEDIUM",
                    message=f"大型案件（¥{opp['amount']:,}）がまだ初期段階「{opp['stage']}」",
                ))

            # 5. まもなくクローズだが確度が低い
            days_to_close = (opp["close_date"] - today).days
            if 0 <= days_to_close <= 14 and opp["probability"] < 0.50:
                alerts.append(self._make_alert(
                    opp=opp,
                    alert_type=ALERT_CLOSING_SOON_LOW_PROB,
                    severity="HIGH",
                    message=f"あと{days_to_close}日でクローズ予定だが確度{opp['probability']*100:.0f}%",
                ))

        # 重要度順 → 金額順でソート
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        alerts.sort(key=lambda a: (severity_order.get(a["severity"], 9), -a["amount"]))

        return alerts

    @staticmethod
    def _make_alert(
        *,
        opp: dict[str, Any],
        alert_type: str,
        severity: str,
        message: str,
    ) -> dict[str, Any]:
        return {
            "opp_id": opp["id"],
            "opp_name": opp["name"],
            "account_name": opp["account_name"],
            "owner_name": opp["owner_name"],
            "amount": opp["amount"],
            "stage": opp["stage"],
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
        }
