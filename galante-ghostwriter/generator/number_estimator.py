"""
AI-powered KPI and budget number estimator.

Generates reasonable estimates for proposal numbers based on
industry benchmarks, client context, and orien data.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("galante_ghostwriter.generator.number_estimator")

ESTIMATOR_SYSTEM_PROMPT = """\
あなたはマーケティング施策の数値見積もり専門家です。

以下のルールに従ってください:
- 業界ベンチマークに基づいた現実的な数値を提示する
- 確信度が低い数値には必ず「[要確認]」を付ける
- 数値の根拠（ベンチマーク、計算ロジック）を簡潔に示す
- 予算は幅を持たせて提示する（例: 500万〜800万円）
- KPIは達成可能かつ意欲的な水準を設定する
"""

ESTIMATOR_USER_PROMPT = """\
以下の提案に対して、KPIと予算の数値見積もりをJSON形式で出力してください。

■ 提案情報
タイトル: {proposal_title}
クライアント: {client_name}
業界: {industry}

■ オリエンの予算・KPI情報
{budget_and_kpi_info}

■ 出力フォーマット（JSON）
{{
  "kpi_estimates": [
    {{
      "metric": "指標名",
      "current": "現状値",
      "target": "目標値",
      "confidence": "high/medium/low",
      "rationale": "根拠"
    }}
  ],
  "budget_breakdown": [
    {{
      "category": "費目",
      "amount_range": "金額レンジ",
      "note": "備考"
    }}
  ],
  "total_budget_range": "総予算レンジ",
  "roi_estimate": "想定ROI"
}}
"""


def _call_ai(system: str, user: str) -> str:
    """Call Claude API with graceful fallback."""
    from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

    if not ANTHROPIC_API_KEY:
        return _placeholder_estimates()

    try:
        import anthropic
    except ImportError:
        return _placeholder_estimates()

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def _placeholder_estimates() -> str:
    """Return placeholder estimates when AI is unavailable."""
    return json.dumps(
        {
            "kpi_estimates": [
                {
                    "metric": "[AI未接続] ブランド認知度",
                    "current": "要確認",
                    "target": "要確認",
                    "confidence": "low",
                    "rationale": "AI接続後に業界ベンチマークから算出",
                }
            ],
            "budget_breakdown": [
                {
                    "category": "[AI未接続] 施策費用",
                    "amount_range": "要確認",
                    "note": "AI接続後に見積もり",
                }
            ],
            "total_budget_range": "[AI未接続] 要確認",
            "roi_estimate": "[AI未接続] 要確認",
        },
        ensure_ascii=False,
        indent=2,
    )


def estimate_numbers(
    plan: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Estimate KPIs and budget numbers for the proposal.

    Parameters
    ----------
    plan : dict
        The proposal plan from the planner.
    context : dict
        The unified context.

    Returns
    -------
    dict
        Structured estimates with KPIs, budget breakdown, and ROI.
    """
    orien = context.get("orien", {})
    budget_info = orien.get("budget_info", "")
    expected_outcomes = orien.get("expected_outcomes", "")
    budget_and_kpi = f"予算情報: {budget_info}\n期待成果: {expected_outcomes}"

    raw = _call_ai(
        ESTIMATOR_SYSTEM_PROMPT,
        ESTIMATOR_USER_PROMPT.format(
            proposal_title=plan.get("proposal_title", ""),
            client_name=context.get("client_name", ""),
            industry=context.get("industry", ""),
            budget_and_kpi_info=budget_and_kpi,
        ),
    )

    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        estimates = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Failed to parse estimator output: %s", raw[:200])
        estimates = json.loads(_placeholder_estimates())
        estimates["_parse_error"] = True

    logger.info("Number estimates generated: %d KPIs", len(estimates.get("kpi_estimates", [])))
    return estimates
