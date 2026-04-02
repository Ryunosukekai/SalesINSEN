"""
Galante's proposal philosophy and framework definitions.

Provides formatted text for AI prompt injection so the model
understands Galante's approach to proposal creation.
"""

from __future__ import annotations

from config import GALANTE_PRINCIPLES, GALANTE_PROPOSAL_FRAMEWORK


def get_principles_text() -> str:
    """Return Galante's 3 principles as formatted text."""
    lines = ["Galante 3つの原則:"]
    for name, desc in GALANTE_PRINCIPLES.items():
        lines.append(f"  {name}: {desc}")
    return "\n".join(lines)


def get_framework_text() -> str:
    """Return the full proposal framework as formatted text for AI context."""
    lines = ["Galante提案フレームワーク（9セクション）:"]
    for section in GALANTE_PROPOSAL_FRAMEWORK["sections"]:
        lines.append(f"\n【{section['title']}】")
        lines.append(f"  説明: {section['description']}")
        lines.append(f"  Galanteアプローチ: {section['galante_approach']}")
    return "\n".join(lines)


def get_tone_guidelines() -> str:
    """Return Galante brand tone guidelines for AI writing."""
    return (
        "Galante執筆トーン・ガイドライン:\n"
        "- 格調高く、知的で、かつ熱量が伝わる文体\n"
        "- 断定調を基本（～である、～と考える）\n"
        "- 抽象論に逃げず、具体的な数値・事例・提案で語る\n"
        "- クライアントへの深い敬意を感じさせる表現\n"
        "- 「御用聞き」的な受動姿勢は排除し、プロとしての見解を示す\n"
        "- カタカナ語の多用を避け、本質を日本語で伝える\n"
        "- 提案書全体に一本の「ストーリーライン」が通っていること"
    )


def get_anti_patterns() -> str:
    """Return common anti-patterns that Galante proposals must avoid."""
    return (
        "Galante提案 NGパターン:\n"
        "- ❌「御用聞き」: クライアントの言葉をそのままなぞるだけの提案\n"
        "- ❌ 施策の羅列: 戦略なき施策リスト（「あれもこれも」型）\n"
        "- ❌ 曖昧な数値: 根拠のないKPI設定\n"
        "- ❌ テンプレ感: どのクライアントにも使える汎用的な文言\n"
        "- ❌ 自社アピール: Galanteの実績自慢が目的化\n"
        "- ❌ 安全策: 無難すぎて心が動かない提案"
    )


def get_section_approach(section_id: str) -> str:
    """Return the Galante approach guidance for a specific section."""
    for section in GALANTE_PROPOSAL_FRAMEWORK["sections"]:
        if section["id"] == section_id:
            return section["galante_approach"]
    return ""
