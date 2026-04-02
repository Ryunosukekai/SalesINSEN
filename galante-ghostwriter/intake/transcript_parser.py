"""
Parse meeting transcription text into usable context.

Transcription text is typically less structured than orien notes.
This module extracts speaker turns and key topics for downstream use.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger("galante_ghostwriter.intake.transcript_parser")


@dataclass
class TranscriptTurn:
    """A single speaker turn in a transcript."""

    speaker: str
    text: str
    timestamp: str = ""


@dataclass
class TranscriptData:
    """Parsed transcript data."""

    raw_text: str = ""
    turns: list[TranscriptTurn] = field(default_factory=list)
    key_quotes: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)


# Common transcript formats:
#   "14:03 田中: ..." or "[田中] ..." or "田中部長: ..."
_TURN_PATTERN = re.compile(
    r"(?:(?P<ts>\d{1,2}:\d{2})\s+)?(?:\[?(?P<speaker>[^\]\[:：]+?)[\]:])\s*(?P<text>.+)"
)

# Phrases that signal important quotes
_KEY_QUOTE_SIGNALS = [
    "重要", "ポイント", "絶対", "必ず", "一番", "最も",
    "したくない", "してほしい", "期待", "懸念", "不安",
    "こだわり", "譲れない", "本音",
]


def parse_transcript(text: str) -> TranscriptData:
    """Parse a meeting transcript into structured data."""
    data = TranscriptData(raw_text=text.strip())

    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        m = _TURN_PATTERN.match(line)
        if m:
            turn = TranscriptTurn(
                speaker=m.group("speaker").strip(),
                text=m.group("text").strip(),
                timestamp=m.group("ts") or "",
            )
            data.turns.append(turn)

            # Check for key quotes
            if any(signal in turn.text for signal in _KEY_QUOTE_SIGNALS):
                data.key_quotes.append(f"{turn.speaker}: {turn.text}")

    # Extract rough topics from section headers or emphasized text
    topic_pattern = re.compile(r"(?:■|▪|●|★|【|◆)\s*(.+?)(?:】|$)")
    for m in topic_pattern.finditer(text):
        topic = m.group(1).strip()
        if topic and topic not in data.topics:
            data.topics.append(topic)

    logger.info(
        "Parsed transcript: %d turns, %d key quotes, %d topics",
        len(data.turns),
        len(data.key_quotes),
        len(data.topics),
    )
    return data
