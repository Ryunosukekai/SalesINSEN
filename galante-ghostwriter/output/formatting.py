"""
Galante brand formatting utilities.

Handles visual identity elements for proposal output.
"""

from __future__ import annotations

from datetime import datetime

# Galante brand colors (for Google Docs formatting)
GALANTE_COLORS = {
    "primary": "#1a1a2e",       # Deep navy
    "accent": "#c9a84c",        # Gold
    "text": "#2d2d2d",          # Near-black
    "subtitle": "#555555",      # Gray
    "background": "#fafafa",    # Off-white
}

# Font preferences
GALANTE_FONTS = {
    "heading_ja": "Noto Sans JP",
    "heading_en": "Montserrat",
    "body_ja": "Noto Sans JP",
    "body_en": "Source Sans Pro",
}


def format_proposal_title(title: str, client_name: str) -> str:
    """Format the proposal title with Galante branding."""
    return f"{title}\n— {client_name} 様 ご提案書 —"


def format_header_block(
    client_name: str,
    proposal_title: str,
    date: str | None = None,
) -> str:
    """Generate the Markdown header block for a proposal."""
    if date is None:
        date = datetime.now().strftime("%Y年%m月%d日")

    return (
        f"# {proposal_title}\n\n"
        f"**{client_name} 様 ご提案書**\n\n"
        f"提出日: {date}  \n"
        f"作成: 株式会社Galante\n\n"
        f"---\n"
    )


def format_section_header(title: str) -> str:
    """Format a section header in Galante style."""
    return f"\n## {title}\n"


def format_quality_badge(score: int, is_acceptable: bool) -> str:
    """Format the quality check result as a status badge."""
    status = "PASS" if is_acceptable else "REVIEW NEEDED"
    return f"\n---\n\n*品質スコア: {score}/10 | ステータス: {status}*\n"


def format_confirmation_list(items: list[str]) -> str:
    """Format the list of items needing confirmation."""
    if not items:
        return ""
    lines = ["\n### 要確認事項\n"]
    for item in items:
        lines.append(f"- [ ] {item}")
    return "\n".join(lines)


def format_footer() -> str:
    """Generate the proposal footer."""
    return (
        "\n---\n\n"
        "*本提案書は株式会社Galanteが作成いたしました。*  \n"
        "*内容に関するご質問・ご要望がございましたら、担当までお気軽にお問い合わせください。*\n"
        "\n"
        f"*Confidential | (C) {datetime.now().year} Galante Inc.*\n"
    )
