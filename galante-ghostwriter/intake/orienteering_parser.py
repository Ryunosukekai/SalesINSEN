"""
Parse orientation meeting notes into structured data.

Handles plain-text notes (from file, stdin, or Google Docs export).
Extracts key fields: background, target, budget, timeline, special notes.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger("galante_ghostwriter.intake.orien_parser")


@dataclass
class OrienData:
    """Structured orientation meeting data."""

    raw_text: str = ""
    client_name: str = ""
    date: str = ""
    attendees: list[str] = field(default_factory=list)
    background: str = ""
    challenges: str = ""
    target_description: str = ""
    budget_info: str = ""
    expected_outcomes: str = ""
    schedule_info: str = ""
    special_notes: str = ""
    extra_sections: dict[str, str] = field(default_factory=dict)


# Section header patterns commonly found in Japanese meeting notes
_SECTION_PATTERNS: list[tuple[str, str]] = [
    (r"(?:■|▪|●|★)\s*背景[・、]?課題", "background"),
    (r"(?:■|▪|●|★)\s*課題", "challenges"),
    (r"(?:■|▪|●|★)\s*ターゲット", "target_description"),
    (r"(?:■|▪|●|★)\s*予算", "budget_info"),
    (r"(?:■|▪|●|★)\s*(?:期待する成果|KPI|目標)", "expected_outcomes"),
    (r"(?:■|▪|●|★)\s*スケジュール", "schedule_info"),
    (r"(?:■|▪|●|★)\s*特記事項", "special_notes"),
]


def parse_orien_text(text: str) -> OrienData:
    """Parse raw orientation text into structured *OrienData*.

    The parser is intentionally lenient — it extracts what it can
    and keeps the full raw text for downstream AI processing.
    """
    data = OrienData(raw_text=text.strip())

    # --- Header metadata ---------------------------------------------------
    date_match = re.search(r"日時[:：]\s*(.+)", text)
    if date_match:
        data.date = date_match.group(1).strip()

    client_match = re.search(r"クライアント[:：]\s*(.+)", text)
    if client_match:
        data.client_name = client_match.group(1).strip()

    attendees_match = re.search(r"出席者[:：]\s*(.+)", text)
    if attendees_match:
        data.attendees = [
            a.strip()
            for a in re.split(r"[/／,、]", attendees_match.group(1))
            if a.strip()
        ]

    # --- Section extraction ------------------------------------------------
    lines = text.split("\n")
    current_field: str | None = None
    current_buf: list[str] = []

    def _flush() -> None:
        nonlocal current_field, current_buf
        if current_field and current_buf:
            content = "\n".join(current_buf).strip()
            if hasattr(data, current_field):
                setattr(data, current_field, content)
            else:
                data.extra_sections[current_field] = content
        current_buf.clear()

    for line in lines:
        matched = False
        for pattern, field_name in _SECTION_PATTERNS:
            if re.search(pattern, line):
                _flush()
                current_field = field_name
                matched = True
                break
        if not matched and current_field is not None:
            current_buf.append(line)

    _flush()

    logger.info("Parsed orien data: client=%s, date=%s", data.client_name, data.date)
    return data


def parse_orien_file(filepath: str) -> OrienData:
    """Read a text file and parse it."""
    with open(filepath, "r", encoding="utf-8") as f:
        return parse_orien_text(f.read())
