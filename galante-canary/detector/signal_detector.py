"""Individual churn signal detection — 11 signal types."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from config import CHURN_SIGNALS

logger = logging.getLogger(__name__)


def _parse_date(value: str | None) -> datetime | None:
    """Parse an ISO-ish date string into a timezone-aware datetime."""
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_signals(
    account: dict[str, Any],
    account_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Run all signal detectors and return a list of triggered signals.

    Each triggered signal dict contains:
      - signal_key: str
      - description: str
      - weight: int
      - severity: str
      - detail: str  (human-readable detail)
    """
    triggered: list[dict[str, Any]] = []
    now = _now()

    opps = account_data.get("opportunities", [])
    pipeline = account_data.get("open_pipeline", [])
    tasks = account_data.get("tasks", [])
    events = account_data.get("events", [])
    emails = account_data.get("emails", [])

    # -- Last contact date ------------------------------------------------
    last_contact = _compute_last_contact(account, tasks, events, emails)
    if last_contact:
        days_since = (now - last_contact).days
        for key, threshold in [
            ("no_contact_90d", 90),
            ("no_contact_60d", 60),
            ("no_contact_30d", 30),
        ]:
            if days_since >= threshold:
                triggered.append(_make_signal(
                    key,
                    f"最終接触: {last_contact.strftime('%Y-%m-%d')} ({days_since}日前)",
                ))
                break  # only the most severe no-contact signal

    # -- Revenue decline --------------------------------------------------
    closed_won = [o for o in opps if o.get("IsWon")]
    if len(closed_won) >= 2:
        amounts = []
        for o in closed_won:
            amt = o.get("Amount")
            if amt is not None:
                amounts.append(float(amt))
        if len(amounts) >= 2:
            latest, previous = amounts[0], amounts[1]
            if previous > 0:
                decline = (previous - latest) / previous
                if decline >= 0.5:
                    triggered.append(_make_signal(
                        "revenue_decline_50",
                        f"発注額: {int(previous):,}円 → {int(latest):,}円 ({decline:.0%}減)",
                    ))
                elif decline >= 0.2:
                    triggered.append(_make_signal(
                        "revenue_decline_20",
                        f"発注額: {int(previous):,}円 → {int(latest):,}円 ({decline:.0%}減)",
                    ))

    # -- Longer cycle -----------------------------------------------------
    closed_dates = []
    for o in closed_won:
        dt = _parse_date(o.get("CloseDate"))
        if dt:
            closed_dates.append(dt)
    if len(closed_dates) >= 3:
        gaps = []
        for i in range(len(closed_dates) - 1):
            gap = abs((closed_dates[i] - closed_dates[i + 1]).days)
            gaps.append(gap)
        if len(gaps) >= 2 and gaps[1] > 0:
            ratio = gaps[0] / gaps[1]
            if ratio >= 1.5:
                triggered.append(_make_signal(
                    "longer_cycle",
                    f"案件間隔: {gaps[1]}日 → {gaps[0]}日 ({ratio:.1f}倍)",
                ))

    # -- No pipeline (regulars only) --------------------------------------
    total_won = len(closed_won)
    if total_won >= 2 and len(pipeline) == 0:
        triggered.append(_make_signal(
            "no_pipeline",
            f"受注実績 {total_won}件の常連クライアントだが進行中案件なし",
        ))

    # -- Meeting decline --------------------------------------------------
    now_dt = now
    q_boundary = now_dt - timedelta(days=90)
    prev_boundary = q_boundary - timedelta(days=90)
    meetings_current = sum(
        1 for e in events
        if (_parse_date(e.get("StartDateTime")) or _parse_date(e.get("CreatedDate")))
        and (_parse_date(e.get("StartDateTime")) or _parse_date(e.get("CreatedDate"))) >= q_boundary  # type: ignore[operator]
    )
    meetings_prev = sum(
        1 for e in events
        if (_parse_date(e.get("StartDateTime")) or _parse_date(e.get("CreatedDate")))
        and prev_boundary <= (_parse_date(e.get("StartDateTime")) or _parse_date(e.get("CreatedDate"))) < q_boundary  # type: ignore[operator]
    )
    if meetings_prev > 0 and meetings_current < meetings_prev:
        triggered.append(_make_signal(
            "meeting_decline",
            f"MTG回数: 前期{meetings_prev}回 → 今期{meetings_current}回",
        ))

    # -- Email no reply ---------------------------------------------------
    outgoing = [e for e in emails if not e.get("Incoming", True)]
    incoming = [e for e in emails if e.get("Incoming", False)]
    if len(outgoing) >= 3:
        last_3_out = outgoing[:3]
        earliest_out = _parse_date(last_3_out[-1].get("MessageDate"))
        has_reply = any(
            _parse_date(inc.get("MessageDate"))
            and earliest_out
            and _parse_date(inc.get("MessageDate")) >= earliest_out  # type: ignore[operator]
            for inc in incoming
        )
        if not has_reply:
            triggered.append(_make_signal(
                "email_no_reply",
                "直近3通の送信メールに返信なし",
            ))

    # -- Recent loss / consecutive losses ---------------------------------
    closed_lost = [o for o in opps if o.get("IsClosed") and not o.get("IsWon")]
    if len(closed_lost) >= 2:
        # Check if the 2 most recent closed are both losses
        recent_closed = sorted(
            [o for o in opps if o.get("IsClosed")],
            key=lambda x: x.get("CloseDate", ""),
            reverse=True,
        )
        if len(recent_closed) >= 2:
            if not recent_closed[0].get("IsWon") and not recent_closed[1].get("IsWon"):
                triggered.append(_make_signal(
                    "consecutive_losses",
                    f"直近2件が連続失注: {recent_closed[0].get('Name')}, {recent_closed[1].get('Name')}",
                ))
            elif not recent_closed[0].get("IsWon"):
                triggered.append(_make_signal(
                    "recent_loss",
                    f"直近の提案が失注: {recent_closed[0].get('Name')}",
                ))
    elif len(closed_lost) == 1:
        most_recent = sorted(
            [o for o in opps if o.get("IsClosed")],
            key=lambda x: x.get("CloseDate", ""),
            reverse=True,
        )
        if most_recent and not most_recent[0].get("IsWon"):
            triggered.append(_make_signal(
                "recent_loss",
                f"直近の提案が失注: {most_recent[0].get('Name')}",
            ))

    return triggered


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_last_contact(
    account: dict,
    tasks: list[dict],
    events: list[dict],
    emails: list[dict],
) -> datetime | None:
    """Determine the last contact date from activities + emails."""
    dates: list[datetime] = []

    # Account.LastActivityDate
    acct_last = _parse_date(account.get("LastActivityDate"))
    if acct_last:
        dates.append(acct_last)

    for t in tasks:
        dt = _parse_date(t.get("ActivityDate")) or _parse_date(t.get("CreatedDate"))
        if dt:
            dates.append(dt)

    for e in events:
        dt = _parse_date(e.get("StartDateTime")) or _parse_date(e.get("CreatedDate"))
        if dt:
            dates.append(dt)

    for em in emails:
        # Only count incoming emails (replies) as actual contact
        if em.get("Incoming", False):
            dt = _parse_date(em.get("MessageDate"))
            if dt:
                dates.append(dt)

    return max(dates) if dates else None


def _make_signal(key: str, detail: str) -> dict[str, Any]:
    """Build a triggered-signal dict."""
    sig = CHURN_SIGNALS[key]
    return {
        "signal_key": key,
        "description": sig["description"],
        "weight": sig["weight"],
        "severity": sig["severity"],
        "detail": detail,
    }
