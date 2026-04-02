"""Salesforce レコードを内部データモデルに変換して取得."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Optional

from config import AppConfig, STAGE_PROBABILITIES
from salesforce.client import SalesforceClient
from salesforce.queries import SOQL

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# データモデル（dataclass ではなく dict ベースで軽量に）
# ---------------------------------------------------------------------------
class DealType:
    NEW = "new"
    EXISTING = "existing"


def make_opportunity(
    *,
    id: str,
    name: str,
    amount: int,
    stage: str,
    close_date: date,
    deal_type: str,
    owner_name: str,
    account_name: str,
    probability: float,
    created_date: date,
    last_activity_date: Optional[date] = None,
    days_since_last_activity: int = 0,
    close_date_change_count: int = 0,
    next_step: Optional[str] = None,
) -> dict[str, Any]:
    """商談レコード辞書を生成."""
    return {
        "id": id,
        "name": name,
        "amount": amount,
        "stage": stage,
        "close_date": close_date,
        "deal_type": deal_type,
        "owner_name": owner_name,
        "account_name": account_name,
        "probability": probability,
        "created_date": created_date,
        "last_activity_date": last_activity_date,
        "days_since_last_activity": days_since_last_activity,
        "close_date_change_count": close_date_change_count,
        "next_step": next_step,
    }


class DataExtractor:
    """Salesforce からデータを取得し、内部モデルに変換."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._client = SalesforceClient(config.salesforce)

    # ------------------------------------------------------------------
    # パイプライン取得
    # ------------------------------------------------------------------
    def fetch_open_pipeline(self, months_ahead: int = 3) -> list[dict[str, Any]]:
        """予測対象のオープン商談を取得."""
        end = _month_end(date.today(), months_ahead)
        soql = SOQL.OPEN_OPPORTUNITIES.format(end_date=end.isoformat())
        records = self._client.query(soql)
        opps = [self._to_opportunity(r) for r in records]

        # クローズ日変更回数を付加
        ids = [o["id"] for o in opps]
        history = self._fetch_close_date_changes(ids)
        for opp in opps:
            opp["close_date_change_count"] = history.get(opp["id"], 0)

        return opps

    def fetch_closed_won_this_month(self) -> list[dict[str, Any]]:
        """今月の受注済み商談を取得."""
        today = date.today()
        month_start = today.replace(day=1)
        month_end = _month_end(today, 0)
        soql = SOQL.CLOSED_WON_THIS_MONTH.format(
            month_start=month_start.isoformat(),
            month_end=month_end.isoformat(),
        )
        records = self._client.query(soql)
        return [self._to_opportunity(r) for r in records]

    def fetch_weekly_won_lost(self) -> tuple[list[dict], list[dict]]:
        """先週の受注/失注商談を取得."""
        today = date.today()
        week_start = today - timedelta(days=today.weekday() + 7)
        week_end = week_start + timedelta(days=6)
        soql = SOQL.WEEKLY_WON_LOST.format(
            week_start=week_start.isoformat(),
            week_end=week_end.isoformat(),
        )
        records = self._client.query(soql)
        won = [self._to_opportunity(r) for r in records if r.get("StageName") == "Closed Won"]
        lost = [self._to_opportunity(r) for r in records if r.get("StageName") == "Closed Lost"]
        return won, lost

    # ------------------------------------------------------------------
    # 内部変換
    # ------------------------------------------------------------------
    def _to_opportunity(self, record: dict) -> dict[str, Any]:
        """Salesforce レコードを内部辞書に変換."""
        stage = record.get("StageName", "")
        probability = (record.get("Probability") or 0) / 100.0
        if stage in STAGE_PROBABILITIES:
            probability = STAGE_PROBABILITIES[stage]

        opp_type = (record.get("Type") or "").lower()
        deal_type = (
            DealType.EXISTING
            if any(kw in opp_type for kw in ("existing", "既存", "renewal", "更新"))
            else DealType.NEW
        )

        close_date = _parse_date(record.get("CloseDate")) or date.today()
        last_activity = _parse_date(record.get("LastActivityDate"))
        created_date = _parse_date(record.get("CreatedDate")) or date.today()
        today = date.today()

        days_since_activity = 0
        if last_activity:
            days_since_activity = (today - last_activity).days
        else:
            days_since_activity = (today - created_date).days

        return make_opportunity(
            id=record["Id"],
            name=record.get("Name", ""),
            amount=int(record.get("Amount") or 0),
            stage=stage,
            close_date=close_date,
            deal_type=deal_type,
            owner_name=_nested(record, "Owner", "Name") or "不明",
            account_name=_nested(record, "Account", "Name") or "不明",
            probability=probability,
            created_date=created_date,
            last_activity_date=last_activity,
            days_since_last_activity=days_since_activity,
            next_step=record.get("NextStep"),
        )

    def _fetch_close_date_changes(self, opp_ids: list[str]) -> dict[str, int]:
        """商談ごとのクローズ日変更回数を取得."""
        if not opp_ids:
            return {}
        ids_str = "','".join(opp_ids)
        soql = SOQL.CLOSE_DATE_HISTORY.format(ids=f"'{ids_str}'")
        try:
            records = self._client.query(soql)
            return {r["OpportunityId"]: r["cnt"] for r in records}
        except Exception as exc:
            logger.warning("CloseDate履歴の取得に失敗: %s", exc)
            return {}


# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------
def _parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _nested(record: dict, *keys: str) -> Optional[str]:
    current: Any = record
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _month_end(base: date, months_ahead: int) -> date:
    month = base.month + months_ahead
    year = base.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    if month == 12:
        return date(year + 1, 1, 1) - timedelta(days=1)
    return date(year, month + 1, 1) - timedelta(days=1)
