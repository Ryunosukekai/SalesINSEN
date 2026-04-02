"""
AI-powered section writer.

Writes each proposal section in Galante's distinctive tone,
guided by the planner's outline.
"""

from __future__ import annotations

import logging
from typing import Any

from knowledge.galante_frameworks import (
    get_section_approach,
    get_tone_guidelines,
)

logger = logging.getLogger("galante_ghostwriter.generator.section_writer")

WRITER_SYSTEM_PROMPT = """\
あなたはGalanteのコピーライターです。

{tone_guidelines}

執筆ルール:
- Galanteのトーン: 格調高く、知的で、かつ熱量が伝わる文体
- 断定調を基本（～である、～と考える）
- 不確かな数値は「[要確認: ○○]」とマーク
- 各セクションは単独でも読めるが、全体のストーリーラインを意識する
- クライアント名を適切に使用し、パーソナライズされた提案にする
- 箇条書きと文章を効果的に使い分ける
"""

WRITER_USER_PROMPT = """\
以下の情報をもとに、提案書の「{section_title}」セクションを執筆してください。

■ 提案書情報
タイトル: {proposal_title}
コアコンセプト: {core_concept}
クライアント: {client_name}
業界: {industry}

■ このセクションのプラン
重要度: {emphasis}
アウトライン:
{outline_text}

Galanteの視点:
{galante_insight}

■ セクション執筆ガイド
{section_approach}

■ オリエンテーション情報（参考）
{orien_text}

■ 出力形式
Markdown形式で出力してください。セクションタイトル（## ）は含めないでください。
本文のみを出力してください。
"""


def _call_ai(system: str, user: str) -> str:
    """Call Claude API with graceful fallback."""
    from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

    if not ANTHROPIC_API_KEY:
        return "[AI未接続] このセクションはAI接続後に自動生成されます。"

    try:
        import anthropic
    except ImportError:
        return "[AI未接続] anthropicライブラリが必要です。"

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def _placeholder_section(section_id: str, plan_section: dict[str, Any]) -> str:
    """Generate placeholder content for a section when AI is unavailable."""
    outline = plan_section.get("outline", [])
    insight = plan_section.get("galante_insight", "")

    lines = [f"[AI未接続] 本セクションはAI接続時に自動生成されます。\n"]
    if outline:
        lines.append("**プランナーのアウトライン:**")
        for item in outline:
            lines.append(f"- {item}")
        lines.append("")
    if insight:
        lines.append(f"**Galanteの視点:** {insight}\n")
    return "\n".join(lines)


def write_section(
    section_id: str,
    plan: dict[str, Any],
    context: dict[str, Any],
) -> str:
    """Write a single proposal section.

    Parameters
    ----------
    section_id : str
        The section ID (e.g. "background", "insight").
    plan : dict
        The full proposal plan from the planner.
    context : dict
        The unified context from ContextAssembler.

    Returns
    -------
    str
        The written section content in Markdown.
    """
    from config import ANTHROPIC_API_KEY

    # Find this section in the plan
    plan_section: dict[str, Any] = {}
    for s in plan.get("sections", []):
        if s.get("id") == section_id:
            plan_section = s
            break

    if not ANTHROPIC_API_KEY:
        return _placeholder_section(section_id, plan_section)

    # Build section metadata
    from knowledge.template_registry import get_section_by_id
    section_def = get_section_by_id(section_id)
    section_title = section_def["title"] if section_def else section_id

    outline_items = plan_section.get("outline", [])
    outline_text = "\n".join(f"- {item}" for item in outline_items) or "（アウトラインなし）"

    system = WRITER_SYSTEM_PROMPT.format(
        tone_guidelines=get_tone_guidelines(),
    )

    user = WRITER_USER_PROMPT.format(
        section_title=section_title,
        proposal_title=plan.get("proposal_title", ""),
        core_concept=plan.get("core_concept", ""),
        client_name=context.get("client_name", ""),
        industry=context.get("industry", ""),
        emphasis=plan_section.get("emphasis", "medium"),
        outline_text=outline_text,
        galante_insight=plan_section.get("galante_insight", ""),
        section_approach=get_section_approach(section_id),
        orien_text=context.get("raw_orien_text", "")[:2000],
    )

    logger.info("Writing section: %s (emphasis: %s)", section_id, plan_section.get("emphasis"))
    return _call_ai(system, user)


def write_all_sections(
    plan: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, str]:
    """Write all sections defined in the plan.

    Returns
    -------
    dict[str, str]
        Mapping of section_id -> written content.
    """
    sections: dict[str, str] = {}
    for plan_section in plan.get("sections", []):
        sid = plan_section["id"]
        sections[sid] = write_section(sid, plan, context)
    logger.info("All %d sections written", len(sections))
    return sections
