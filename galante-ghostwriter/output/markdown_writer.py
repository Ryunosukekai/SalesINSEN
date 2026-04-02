"""
Write proposal output as a Markdown file.

This is the default (always-available) output format.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from knowledge.template_registry import get_section_by_id
from .formatting import (
    format_confirmation_list,
    format_footer,
    format_header_block,
    format_quality_badge,
    format_section_header,
)

logger = logging.getLogger("galante_ghostwriter.output.markdown_writer")


def render_proposal_markdown(
    plan: dict[str, Any],
    sections: dict[str, str],
    quality: dict[str, Any],
    context: dict[str, Any],
) -> str:
    """Render a complete proposal as Markdown.

    Parameters
    ----------
    plan : dict
        The proposal plan from the planner.
    sections : dict[str, str]
        Written section contents keyed by section ID.
    quality : dict
        Quality check results.
    context : dict
        The unified context.

    Returns
    -------
    str
        The full Markdown document.
    """
    client_name = context.get("client_name", "クライアント")
    proposal_title = plan.get("proposal_title", "ご提案書")

    parts: list[str] = []

    # Header
    parts.append(format_header_block(client_name, proposal_title))

    # Core concept
    core_concept = plan.get("core_concept", "")
    if core_concept:
        parts.append(f"\n> **コアコンセプト:** {core_concept}\n")

    # Sections
    for plan_section in plan.get("sections", []):
        sid = plan_section["id"]
        sec_def = get_section_by_id(sid)
        title = sec_def["title"] if sec_def else sid

        parts.append(format_section_header(title))

        content = sections.get(sid, "[未生成]")
        parts.append(content)

    # Quality badge
    parts.append(
        format_quality_badge(
            quality.get("overall_score", 0),
            quality.get("is_acceptable", False),
        )
    )

    # Confirmation items
    needs_conf = quality.get("needs_confirmation", [])
    # Also extract [要確認] markers from section content
    for content in sections.values():
        import re
        for m in re.finditer(r"\[要確認[:：]\s*([^\]]+)\]", content):
            item = m.group(1).strip()
            if item not in needs_conf:
                needs_conf.append(item)

    if needs_conf:
        parts.append(format_confirmation_list(needs_conf))

    # Footer
    parts.append(format_footer())

    return "\n".join(parts)


def write_proposal_file(
    markdown: str,
    client_name: str,
    output_dir: str | Path | None = None,
) -> Path:
    """Write the Markdown proposal to a file.

    Parameters
    ----------
    markdown : str
        The rendered Markdown content.
    client_name : str
        Client name (used in filename).
    output_dir : Path, optional
        Output directory. Defaults to project output/ dir.

    Returns
    -------
    Path
        Path to the written file.
    """
    if output_dir is None:
        from config import BASE_DIR
        output_dir = BASE_DIR / "output"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = client_name.replace(" ", "_").replace("/", "_")
    filename = f"proposal_{safe_name}_{timestamp}.md"
    filepath = output_dir / filename

    filepath.write_text(markdown, encoding="utf-8")
    logger.info("Proposal written to: %s", filepath)
    return filepath
