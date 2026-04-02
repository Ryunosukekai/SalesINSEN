"""
Search and retrieve past proposal knowledge from the reference base.

Provides similarity matching by industry, type, and keyword overlap
so the AI planner can reference relevant past work.
"""

from __future__ import annotations

import logging
from typing import Any

from config import REFERENCE_PROPOSALS

logger = logging.getLogger("galante_ghostwriter.knowledge.past_proposals")


def search_proposals(
    industry: str = "",
    proposal_type: str = "",
    keywords: list[str] | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Search reference proposals by industry, type, and keywords.

    Returns up to *limit* proposals ranked by relevance (simple scoring).
    """
    keywords = keywords or []
    scored: list[tuple[float, str, dict[str, Any]]] = []

    for key, proposal in REFERENCE_PROPOSALS.items():
        score = 0.0

        # Industry match
        if industry and industry in proposal.get("industry", ""):
            score += 3.0
        if proposal.get("industry") == "全般":
            score += 1.0

        # Type match
        if proposal_type and proposal_type == proposal.get("type"):
            score += 2.0

        # Keyword overlap (check title, key_concept, sections_summary values)
        searchable = " ".join([
            proposal.get("title", ""),
            proposal.get("key_concept", ""),
            " ".join(proposal.get("sections_summary", {}).values()),
        ])
        for kw in keywords:
            if kw in searchable:
                score += 1.5

        scored.append((score, key, proposal))

    # Sort descending by score
    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, key, proposal in scored[:limit]:
        if score > 0:
            results.append({**proposal, "_key": key, "_score": score})

    logger.info(
        "Searched proposals: industry=%s, type=%s, keywords=%s -> %d results",
        industry,
        proposal_type,
        keywords,
        len(results),
    )
    return results


def get_proposal_by_key(key: str) -> dict[str, Any] | None:
    """Retrieve a specific reference proposal by its key."""
    return REFERENCE_PROPOSALS.get(key)


def get_proposal_summary_text(proposals: list[dict[str, Any]]) -> str:
    """Format reference proposals into a text block for AI context."""
    if not proposals:
        return "（参考提案なし）"

    parts: list[str] = []
    for i, p in enumerate(proposals, 1):
        summary = p.get("sections_summary", {})
        summary_lines = "\n".join(
            f"    - {k}: {v}" for k, v in summary.items()
        )
        parts.append(
            f"【参考提案{i}】{p.get('title', '不明')}\n"
            f"  タイプ: {p.get('type', '不明')}\n"
            f"  業界: {p.get('industry', '不明')}\n"
            f"  コアコンセプト: {p.get('key_concept', '不明')}\n"
            f"  セクション概要:\n{summary_lines}"
        )
    return "\n\n".join(parts)
