"""
Manage proposal templates.

Templates define the structure (section order, formatting hints)
for different proposal types.
"""

from __future__ import annotations

import logging
from typing import Any

from config import GALANTE_PROPOSAL_FRAMEWORK, TEMPLATES

logger = logging.getLogger("galante_ghostwriter.knowledge.template_registry")


def get_template_doc_id(template_key: str = "unified_template") -> str | None:
    """Return the Google Docs template ID for a given key."""
    return TEMPLATES.get(template_key)


def get_section_definitions() -> list[dict[str, Any]]:
    """Return the ordered list of section definitions from the framework."""
    return GALANTE_PROPOSAL_FRAMEWORK["sections"]


def get_section_by_id(section_id: str) -> dict[str, Any] | None:
    """Look up a single section definition by its ID."""
    for section in GALANTE_PROPOSAL_FRAMEWORK["sections"]:
        if section["id"] == section_id:
            return section
    return None


def get_section_ids() -> list[str]:
    """Return ordered section IDs."""
    return [s["id"] for s in GALANTE_PROPOSAL_FRAMEWORK["sections"]]


def build_template_context(proposal_type: str = "general") -> dict[str, Any]:
    """Build a template context dict suitable for Jinja2 rendering.

    Parameters
    ----------
    proposal_type : str
        E.g. "influencer", "digital", "branding", "general".

    Returns
    -------
    dict
        Template metadata including sections, type, and formatting hints.
    """
    sections = get_section_definitions()

    # Type-specific emphasis hints
    emphasis_overrides: dict[str, dict[str, str]] = {
        "influencer": {"target": "high", "insight": "high", "message": "high"},
        "digital": {"success": "high", "budget": "high"},
        "branding": {"insight": "high", "message": "high", "from_to": "high"},
    }

    overrides = emphasis_overrides.get(proposal_type, {})

    template_sections = []
    for s in sections:
        ts = {**s, "default_emphasis": overrides.get(s["id"], "medium")}
        template_sections.append(ts)

    return {
        "proposal_type": proposal_type,
        "sections": template_sections,
        "template_doc_id": get_template_doc_id(),
    }
