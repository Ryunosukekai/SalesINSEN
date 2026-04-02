"""Fetch and transform Salesforce data for churn analysis."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from salesforce.client import get_client
from salesforce import queries

logger = logging.getLogger(__name__)


def _query(soql: str) -> list[dict[str, Any]]:
    """Execute a SOQL query and return records as dicts."""
    sf = get_client()
    result = sf.query_all(soql)
    return result.get("records", [])


def _strip_attributes(records: list[dict]) -> list[dict]:
    """Remove Salesforce metadata keys from records."""
    cleaned: list[dict] = []
    for rec in records:
        row = {}
        for k, v in rec.items():
            if k == "attributes":
                continue
            if isinstance(v, dict) and "attributes" in v:
                v = {kk: vv for kk, vv in v.items() if kk != "attributes"}
            row[k] = v
        cleaned.append(row)
    return cleaned


def fetch_active_accounts() -> list[dict[str, Any]]:
    """Fetch all active customer / partner accounts."""
    logger.info("有効な取引先を取得中...")
    raw = _query(queries.QUERY_ACTIVE_ACCOUNTS)
    accounts = _strip_attributes(raw)
    logger.info("取引先 %d 件取得完了", len(accounts))
    return accounts


def fetch_account_data(account_id: str) -> dict[str, Any]:
    """Fetch all relevant data for a single account."""
    opps = _strip_attributes(
        _query(queries.QUERY_RECENT_OPPORTUNITIES.format(account_id=account_id))
    )
    pipeline = _strip_attributes(
        _query(queries.QUERY_OPEN_PIPELINE.format(account_id=account_id))
    )
    tasks = _strip_attributes(
        _query(queries.QUERY_RECENT_TASKS.format(account_id=account_id))
    )
    events = _strip_attributes(
        _query(queries.QUERY_RECENT_EVENTS.format(account_id=account_id))
    )

    # Emails may not be available in all orgs
    emails: list[dict] = []
    try:
        emails = _strip_attributes(
            _query(queries.QUERY_RECENT_EMAILS.format(account_id=account_id))
        )
    except Exception:
        logger.debug("EmailMessage が利用できません (account=%s)", account_id)

    return {
        "opportunities": opps,
        "open_pipeline": pipeline,
        "tasks": tasks,
        "events": events,
        "emails": emails,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
