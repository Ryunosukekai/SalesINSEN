"""Salesforce data fetcher for pipeline opportunities."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from simple_salesforce import Salesforce

from .config import AgentConfig
from .models import DealType, Opportunity

logger = logging.getLogger(__name__)


class SalesforceClient:
    """Fetches and transforms Salesforce Opportunity data."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._sf: Optional[Salesforce] = None

    def connect(self) -> None:
        """Establish connection to Salesforce."""
        from simple_salesforce import Salesforce

        sf_config = self.config.salesforce
        logger.info("Connecting to Salesforce (domain=%s)...", sf_config.domain)
        self._sf = Salesforce(
            username=sf_config.username,
            password=sf_config.password,
            security_token=sf_config.security_token,
            domain=sf_config.domain,
            version=sf_config.api_version,
        )
        logger.info("Connected to Salesforce successfully.")

    @property
    def sf(self) -> Salesforce:
        if self._sf is None:
            self.connect()
        return self._sf

    def fetch_open_opportunities(self, months_ahead: int = 3) -> list[Opportunity]:
        """Fetch all open opportunities closing within the forecast horizon."""
        end_date = _month_end(months_ahead)
        query = f"""
            SELECT
                Id, Name, Amount, StageName, CloseDate,
                Type, Owner.Name, Account.Name, Probability,
                CreatedDate, LastActivityDate, NextStep
            FROM Opportunity
            WHERE IsClosed = false
              AND CloseDate <= {end_date.isoformat()}
            ORDER BY CloseDate ASC
        """
        logger.info("Querying Salesforce opportunities (through %s)...", end_date)
        result = self.sf.query_all(query)
        records = result.get("records", [])
        logger.info("Fetched %d open opportunities.", len(records))

        opportunities = [self._to_opportunity(r) for r in records]
        return opportunities

    def fetch_close_date_history(self, opportunity_ids: list[str]) -> dict[str, int]:
        """Fetch how many times CloseDate was changed per opportunity."""
        if not opportunity_ids:
            return {}

        ids_str = "','".join(opportunity_ids)
        query = f"""
            SELECT OpportunityId, COUNT(Id) cnt
            FROM OpportunityFieldHistory
            WHERE Field = 'CloseDate'
              AND OpportunityId IN ('{ids_str}')
            GROUP BY OpportunityId
        """
        try:
            result = self.sf.query_all(query)
            return {
                r["OpportunityId"]: r["cnt"] for r in result.get("records", [])
            }
        except Exception as e:
            logger.warning("Could not fetch field history (may not be enabled): %s", e)
            return {}

    def _to_opportunity(self, record: dict) -> Opportunity:
        """Convert a Salesforce record to an Opportunity model."""
        stage = record.get("StageName", "")
        probability = (record.get("Probability") or 0) / 100.0
        stage_probs = self.config.forecast.stage_probabilities
        if stage in stage_probs:
            probability = stage_probs[stage]

        opp_type = (record.get("Type") or "").lower()
        deal_type = (
            DealType.EXISTING
            if "existing" in opp_type or "既存" in opp_type or "renewal" in opp_type
            else DealType.NEW
        )

        close_date = _parse_date(record.get("CloseDate"))
        last_activity = _parse_date(record.get("LastActivityDate"))
        created_date = _parse_date(record.get("CreatedDate"))

        days_since_activity = 0
        if last_activity:
            days_since_activity = (date.today() - last_activity).days
        elif created_date:
            days_since_activity = (date.today() - created_date).days

        return Opportunity(
            id=record["Id"],
            name=record.get("Name", ""),
            amount=record.get("Amount") or 0,
            stage=stage,
            close_date=close_date or date.today(),
            deal_type=deal_type,
            owner_name=_nested_get(record, "Owner", "Name") or "不明",
            account_name=_nested_get(record, "Account", "Name") or "不明",
            probability=probability,
            created_date=created_date or date.today(),
            last_activity_date=last_activity,
            days_since_last_activity=days_since_activity,
            next_step=record.get("NextStep"),
        )


def _parse_date(value) -> Optional[date]:
    """Parse a Salesforce date string to a Python date."""
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _nested_get(record: dict, *keys) -> Optional[str]:
    """Safely get a nested value from a Salesforce record."""
    current = record
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _month_end(months_ahead: int) -> date:
    """Get the last day of the month N months from now."""
    today = date.today()
    month = today.month + months_ahead
    year = today.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    # First day of next month minus 1 day
    if month == 12:
        return date(year + 1, 1, 1) - timedelta(days=1)
    return date(year, month + 1, 1) - timedelta(days=1)
