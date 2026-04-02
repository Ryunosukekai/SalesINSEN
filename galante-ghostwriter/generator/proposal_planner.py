"""
AI-powered proposal structure planner.

Decides section emphasis, generates outlines, and flags missing information.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from knowledge.galante_frameworks import (
    get_anti_patterns,
    get_framework_text,
    get_principles_text,
)
from knowledge.past_proposals import get_proposal_summary_text, search_proposals

logger = logging.getLogger("galante_ghostwriter.generator.planner")

PLANNER_SYSTEM_PROMPT = """\
あなたはGalanteの提案戦略プランナーです。

{principles}

{framework}

{anti_patterns}
"""

PLANNER_USER_PROMPT = """\
以下のオリエンテーション情報をもとに、提案書の構成プランをJSON形式で出力してください。

■ クライアント情報
クライアント名: {client_name}
業界: {industry}
提案タイプ: {proposal_type}

■ オリエンテーション内容
{orien_text}

■ 参考提案
{reference_text}

■ 出力フォーマット（JSON）
以下の構造で出力してください。JSON以外のテキストは出力しないでください。

{{
  "proposal_title": "提案書タイトル",
  "core_concept": "提案のコアコンセプト（一言）",
  "sections": [
    {{
      "id": "セクションID",
      "emphasis": "high/medium/low",
      "outline": ["アウトラインポイント1", "ポイント2", "..."],
      "galante_insight": "このセクションでのGalanteならではの切り口",
      "missing_info": ["不足している情報1", "..."]
    }}
  ],
  "differentiator": "他社提案との差別化ポイント",
  "risk_note": "提案上のリスク・注意点"
}}
"""


def _call_ai(system: str, user: str) -> str:
    """Call Claude API with graceful fallback."""
    from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY未設定 — プレースホルダーを返します")
        return _placeholder_plan()

    try:
        import anthropic
    except ImportError:
        logger.warning("anthropicライブラリ未インストール — プレースホルダーを返します")
        return _placeholder_plan()

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def _placeholder_plan() -> str:
    """Return a placeholder plan JSON when AI is unavailable."""
    from config import GALANTE_PROPOSAL_FRAMEWORK

    sections = []
    for s in GALANTE_PROPOSAL_FRAMEWORK["sections"]:
        sections.append({
            "id": s["id"],
            "emphasis": "medium",
            "outline": [f"[AI未接続] {s['description']}の概要を記述"],
            "galante_insight": f"[AI未接続] {s['title']}におけるGalanteの視点",
            "missing_info": [],
        })

    plan = {
        "proposal_title": "[AI未接続] 提案書タイトル",
        "core_concept": "[AI未接続] コアコンセプト",
        "sections": sections,
        "differentiator": "[AI未接続] 差別化ポイント",
        "risk_note": "[AI未接続] リスク・注意点",
    }
    return json.dumps(plan, ensure_ascii=False, indent=2)


def plan_proposal(context: dict[str, Any]) -> dict[str, Any]:
    """Generate a proposal structure plan from assembled context.

    Parameters
    ----------
    context : dict
        The unified context from ContextAssembler.assemble().

    Returns
    -------
    dict
        The structured plan (parsed JSON).
    """
    client_name = context.get("client_name", "不明")
    industry = context.get("industry", "不明")
    proposal_type = context.get("proposal_type", "general")
    orien_text = context.get("raw_orien_text", "（オリエン情報なし）")

    # Find relevant past proposals
    past = search_proposals(
        industry=industry,
        proposal_type=proposal_type,
        keywords=[client_name],
    )
    reference_text = context.get("reference_text", "")
    if not reference_text:
        reference_text = get_proposal_summary_text(past)

    system = PLANNER_SYSTEM_PROMPT.format(
        principles=get_principles_text(),
        framework=get_framework_text(),
        anti_patterns=get_anti_patterns(),
    )

    user = PLANNER_USER_PROMPT.format(
        client_name=client_name,
        industry=industry,
        proposal_type=proposal_type,
        orien_text=orien_text,
        reference_text=reference_text,
    )

    logger.info("Planning proposal for %s (%s)", client_name, industry)
    raw = _call_ai(system, user)

    # Parse JSON from response (handle markdown code fences)
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        plan = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Failed to parse planner output as JSON: %s", raw[:200])
        plan = json.loads(_placeholder_plan())
        plan["_parse_error"] = True

    logger.info("Plan generated: title=%s", plan.get("proposal_title", "?"))
    return plan
