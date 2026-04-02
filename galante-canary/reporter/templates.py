"""Message templates for Galante Canary alerts."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _group_by_range(results: list[dict[str, Any]]) -> dict[str, list[dict]]:
    """Group scored results by risk label."""
    groups: dict[str, list[dict]] = {
        "\U0001f6a8": [],  # 緊急 81-100
        "\U0001f534": [],  # 危険 61-80
        "\U0001f7e0": [],  # 警戒 41-60
        "\U0001f7e1": [],  # 注意 21-40
        "\U0001f7e2": [],  # 健全 0-20
    }
    for r in results:
        emoji = r.get("emoji", "\U0001f7e2")
        if emoji in groups:
            groups[emoji].append(r)
    return groups


def _format_account_line(r: dict[str, Any], include_prescription: bool = True) -> str:
    """Format a single account entry for the alert."""
    line = f"\u251c {r['account_name']} \u2014 \u30b9\u30b3\u30a2: {r['score']}/100 \u2014 \u62c5\u5f53: {r['owner_name']}"
    line += f"\n\u2502 \u30b7\u30b0\u30ca\u30eb: {r['signal_summary']}"
    if include_prescription and r.get("prescription"):
        p = r["prescription"]
        diag = p.get("diagnosis", "")
        if diag:
            line += f"\n\u2502 \u51e6\u65b9\u7b8b: {diag}"
        action = p.get("immediate_action", {})
        if isinstance(action, dict) and action.get("action"):
            line += f"\n\u2502 \u2192 {action['action']} ({action.get('timing', '')})"
    return line


def build_daily_alert(
    results: list[dict[str, Any]],
    date_str: str | None = None,
) -> str:
    """Build the full daily Slack alert message.

    Only includes accounts with score >= 40 in the detailed section.
    Always includes the summary section.
    """
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    total = len(results)
    groups = _group_by_range(results)

    lines: list[str] = [
        "\U0001f424 *Galante Canary \u2014 \u96e2\u53cd\u4e88\u5146\u30a2\u30e9\u30fc\u30c8*",
        "\u2501" * 18,
        "",
        f"\U0001f4c5 {date_str} | \u76e3\u8996\u30a2\u30ab\u30a6\u30f3\u30c8\u6570: {total}\u793e",
        "",
    ]

    # 緊急 section
    section_map = [
        ("\U0001f6a8", "\u7dca\u6025", "\u30b9\u30b3\u30a281-100"),
        ("\U0001f534", "\u5371\u967a", "\u30b9\u30b3\u30a261-80"),
        ("\U0001f7e0", "\u8b66\u6212", "\u30b9\u30b3\u30a241-60"),
    ]

    for emoji, label, range_str in section_map:
        accounts = groups.get(emoji, [])
        lines.append(f"*\u3010{emoji} {label}\uff08{range_str}\uff09\u3011*")
        if accounts:
            for acct in accounts:
                lines.append(_format_account_line(acct))
        else:
            lines.append("\u251c \u8a72\u5f53\u306a\u3057")
        lines.append("")

    # Summary
    lines.append("*\u3010\U0001f4ca \u5168\u4f53\u30b5\u30de\u30ea\u30fc\u3011*")
    summary_items = [
        ("\U0001f7e2", "\u5065\u5168", groups.get("\U0001f7e2", [])),
        ("\U0001f7e1", "\u6ce8\u610f", groups.get("\U0001f7e1", [])),
        ("\U0001f7e0", "\u8b66\u6212", groups.get("\U0001f7e0", [])),
        ("\U0001f534", "\u5371\u967a", groups.get("\U0001f534", [])),
        ("\U0001f6a8", "\u7dca\u6025", groups.get("\U0001f6a8", [])),
    ]
    for i, (emoji, label, accts) in enumerate(summary_items):
        prefix = "\u2514" if i == len(summary_items) - 1 else "\u251c"
        lines.append(f"{prefix} {emoji} {label}: {len(accts)}\u793e")

    lines.append("")
    lines.append("_Powered by Galante Canary \U0001f424_")

    return "\n".join(lines)


def build_account_report(result: dict[str, Any]) -> str:
    """Build a detailed single-account report."""
    lines: list[str] = [
        f"{result['emoji']} *{result['account_name']}* \u2014 \u30b9\u30b3\u30a2: {result['score']}/100 ({result['label']})",
        f"\u62c5\u5f53: {result['owner_name']}",
        "",
    ]

    if result.get("signals"):
        lines.append("*\u691c\u51fa\u30b7\u30b0\u30ca\u30eb:*")
        for s in result["signals"]:
            sev = s["severity"].upper()
            lines.append(f"  [{sev}] {s['description']}: {s.get('detail', '')}")
        lines.append("")

    trend = result.get("trend")
    if trend:
        lines.append(f"*\u30c8\u30ec\u30f3\u30c9:* {trend.get('detail', '')}")
        lines.append("")

    prescription = result.get("prescription")
    if prescription:
        lines.append("*AI\u51e6\u65b9\u7b8b:*")
        lines.append(f"  \u8a3a\u65ad: {prescription.get('diagnosis', '')}")
        lines.append(f"  \u539f\u56e0\u4eee\u8aac: {prescription.get('root_cause_hypothesis', '')}")
        action = prescription.get("immediate_action", {})
        if isinstance(action, dict):
            lines.append(f"  \u5373\u6642\u30a2\u30af\u30b7\u30e7\u30f3: {action.get('action', '')} ({action.get('timing', '')})")
            lines.append(f"  \u30c8\u30fc\u30af: {action.get('script', '')}")
        plan = prescription.get("follow_up_plan", {})
        if isinstance(plan, dict):
            lines.append(f"  Week 1: {plan.get('week1', '')}")
            lines.append(f"  Week 2: {plan.get('week2', '')}")
            lines.append(f"  Month 1: {plan.get('month1', '')}")
        lines.append(f"  \u4fa1\u5024\u63d0\u4f9b: {prescription.get('value_offering', '')}")
        if prescription.get("escalation_needed"):
            lines.append(f"  \u26a0\ufe0f \u30a8\u30b9\u30ab\u30ec: {prescription.get('escalation_reason', '')}")

    return "\n".join(lines)
