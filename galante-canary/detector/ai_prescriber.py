"""AI Prescriber — Claude API でフォローアップ処方箋を生成."""
from __future__ import annotations

import json
import logging
from typing import Any

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
あなたはGalanteの顧客リレーション戦略の専門家です。

【Galanteのフォロー哲学】
- 「催促」ではなく「価値提供」でリエンゲージ
- 「御用聞き」ではなく「気づきの提供」でコンタクト
- 過去施策のレポートや業界情報を「お土産」として持っていく
- 「納品=次回提案」原則に基づき、前回施策の振り返りから入る
- ロイヤルカスタマー（300万円以上）は訪問提案を基本

以下の情報をもとに、具体的なフォローアップ処方箋をJSON形式で出力してください。

Output JSON (このフォーマット厳守):
{
  "diagnosis": "現状の診断",
  "root_cause_hypothesis": "離反原因の仮説",
  "immediate_action": {"action": "すぐ取るべきアクション", "script": "具体的なトークスクリプト", "timing": "タイミング"},
  "follow_up_plan": {"week1": "1週間後のアクション", "week2": "2週間後のアクション", "month1": "1ヶ月後のアクション"},
  "value_offering": "価値提供の内容",
  "escalation_needed": false,
  "escalation_reason": ""
}
"""


def _placeholder_prescription(account_name: str, score: int, signals: list[dict]) -> dict[str, Any]:
    """Return a static placeholder when Claude API is unavailable."""
    signal_names = [s["description"] for s in signals]
    is_critical = score >= 61

    return {
        "diagnosis": f"{account_name}は離反リスクスコア{score}/100。検出シグナル: {', '.join(signal_names)}",
        "root_cause_hypothesis": "接触頻度の低下とパイプライン不足が主因と推定",
        "immediate_action": {
            "action": "訪問アポイント設定" if is_critical else "メールでのコンタクト",
            "script": f"「{account_name}様、先日の施策の振り返りレポートをお持ちしたく...」",
            "timing": "本日中" if is_critical else "今週中",
        },
        "follow_up_plan": {
            "week1": "前回施策の振り返りレポート送付",
            "week2": "業界トレンド情報の共有",
            "month1": "次回施策の提案MTG設定",
        },
        "value_offering": "前回施策の効果測定レポートと業界ベンチマーク比較資料",
        "escalation_needed": is_critical,
        "escalation_reason": "スコア61以上のため上長確認推奨" if is_critical else "",
    }


def generate_prescription(
    account: dict[str, Any],
    score_result: dict[str, Any],
) -> dict[str, Any]:
    """Generate an AI-powered follow-up prescription.

    Falls back to a placeholder if ANTHROPIC_API_KEY is not set.
    """
    account_name = score_result.get("account_name", "不明")
    score = score_result.get("score", 0)
    signals = score_result.get("signals", [])

    if not ANTHROPIC_API_KEY:
        logger.info("ANTHROPIC_API_KEY 未設定 — プレースホルダー処方箋を使用")
        return _placeholder_prescription(account_name, score, signals)

    try:
        import anthropic  # noqa: WPS433
    except ImportError:
        logger.warning("anthropic パッケージ未インストール — プレースホルダー使用")
        return _placeholder_prescription(account_name, score, signals)

    # Build user prompt
    owner_name = score_result.get("owner_name", "不明")
    signal_details = "\n".join(
        f"- [{s['severity'].upper()}] {s['description']}: {s.get('detail', '')}"
        for s in signals
    )
    annual_revenue = account.get("AnnualRevenue")
    revenue_str = f"{int(annual_revenue):,}円" if annual_revenue else "不明"

    user_prompt = f"""\
【クライアント情報】
- 会社名: {account_name}
- 担当者: {owner_name}
- 年間取引額: {revenue_str}
- 業種: {account.get('Industry', '不明')}

【離反リスクスコア】{score}/100 ({score_result.get('label', '')})

【検出シグナル】
{signal_details}

上記の情報に基づき、具体的なフォローアップ処方箋をJSON形式で出力してください。
"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        content = response.content[0].text

        # Extract JSON from response
        # Try to find JSON block in the response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        prescription = json.loads(content)
        logger.info("AI処方箋を生成しました: %s", account_name)
        return prescription

    except json.JSONDecodeError:
        logger.warning("AI応答のJSON解析に失敗 — プレースホルダー使用")
        return _placeholder_prescription(account_name, score, signals)
    except Exception as exc:
        logger.warning("AI処方箋生成エラー: %s — プレースホルダー使用", exc)
        return _placeholder_prescription(account_name, score, signals)
