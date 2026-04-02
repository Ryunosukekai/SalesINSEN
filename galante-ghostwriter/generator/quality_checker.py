"""
AI-powered quality checker.

Verifies the generated proposal against Galante's 3 principles
(PASSIONE, SFIDA, RISPETTO), checks for hidden insights,
validates numbers, and flags issues.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from knowledge.galante_frameworks import (
    get_anti_patterns,
    get_principles_text,
)

logger = logging.getLogger("galante_ghostwriter.generator.quality_checker")

CHECKER_SYSTEM_PROMPT = """\
あなたはGalanteの提案品質チェッカーです。

{principles}

{anti_patterns}

あなたの役割は、生成された提案書が上記の原則を満たし、
NGパターンに該当しないかを厳しくチェックすることです。
"""

CHECKER_USER_PROMPT = """\
以下の提案書ドラフトを品質チェックしてください。

■ 提案書タイトル: {proposal_title}
■ クライアント: {client_name}
■ 業界: {industry}

■ 提案書本文
{proposal_text}

■ チェック観点
1. PASSIONE（情熱）: クライアントの課題に本気で向き合っているか
2. SFIDA（挑戦）: 大胆で市場を動かす提案になっているか
3. RISPETTO（敬意）: ブランド・歴史への敬意があるか
4. 「御用聞き」になっていないか（課題の再定義ができているか）
5. 隠れたインサイトがあるか（クライアントが気づいていない視点）
6. 数値の妥当性（[要確認]マークの確認）
7. ストーリーラインの一貫性

■ 出力フォーマット（JSON）
{{
  "overall_score": 1-10の評価,
  "principle_check": {{
    "passione": {{"score": 1-10, "comment": "コメント"}},
    "sfida": {{"score": 1-10, "comment": "コメント"}},
    "rispetto": {{"score": 1-10, "comment": "コメント"}}
  }},
  "strengths": ["強み1", "強み2"],
  "issues": [
    {{
      "severity": "high/medium/low",
      "section": "セクションID",
      "issue": "問題の内容",
      "suggestion": "改善提案"
    }}
  ],
  "needs_confirmation": ["[要確認]項目のリスト"],
  "is_acceptable": true/false,
  "summary": "総評コメント"
}}
"""


def _call_ai(system: str, user: str) -> str:
    """Call Claude API with graceful fallback."""
    from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

    if not ANTHROPIC_API_KEY:
        return _placeholder_check()

    try:
        import anthropic
    except ImportError:
        return _placeholder_check()

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def _placeholder_check() -> str:
    """Return placeholder quality check when AI is unavailable."""
    return json.dumps(
        {
            "overall_score": 0,
            "principle_check": {
                "passione": {"score": 0, "comment": "[AI未接続] チェック未実施"},
                "sfida": {"score": 0, "comment": "[AI未接続] チェック未実施"},
                "rispetto": {"score": 0, "comment": "[AI未接続] チェック未実施"},
            },
            "strengths": ["[AI未接続] 品質チェック未実施"],
            "issues": [],
            "needs_confirmation": [],
            "is_acceptable": False,
            "summary": "[AI未接続] AI接続後に品質チェックを実施してください。",
        },
        ensure_ascii=False,
        indent=2,
    )


def check_quality(
    sections: dict[str, str],
    plan: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Run quality checks on the generated proposal.

    Parameters
    ----------
    sections : dict[str, str]
        Written section contents keyed by section ID.
    plan : dict
        The proposal plan.
    context : dict
        The unified context.

    Returns
    -------
    dict
        Quality check results with scores, issues, and recommendations.
    """
    # Assemble full proposal text for checking
    from knowledge.template_registry import get_section_by_id

    proposal_parts: list[str] = []
    for sid, content in sections.items():
        sec_def = get_section_by_id(sid)
        title = sec_def["title"] if sec_def else sid
        proposal_parts.append(f"## {title}\n\n{content}")

    proposal_text = "\n\n---\n\n".join(proposal_parts)

    system = CHECKER_SYSTEM_PROMPT.format(
        principles=get_principles_text(),
        anti_patterns=get_anti_patterns(),
    )

    user = CHECKER_USER_PROMPT.format(
        proposal_title=plan.get("proposal_title", ""),
        client_name=context.get("client_name", ""),
        industry=context.get("industry", ""),
        proposal_text=proposal_text[:8000],  # Truncate if very long
    )

    logger.info("Running quality check on proposal")
    raw = _call_ai(system, user)

    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Failed to parse quality check output: %s", raw[:200])
        result = json.loads(_placeholder_check())
        result["_parse_error"] = True

    logger.info(
        "Quality check complete: score=%s, acceptable=%s",
        result.get("overall_score"),
        result.get("is_acceptable"),
    )
    return result
