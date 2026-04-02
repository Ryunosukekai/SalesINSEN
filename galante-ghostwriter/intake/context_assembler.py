"""
Merge all intake inputs into a single structured context dict
that downstream pipeline stages consume.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

from .orienteering_parser import OrienData, parse_orien_file, parse_orien_text
from .transcript_parser import TranscriptData, parse_transcript

logger = logging.getLogger("galante_ghostwriter.intake.context_assembler")


class ContextAssembler:
    """Assemble a unified context dict from heterogeneous inputs."""

    def __init__(
        self,
        client_name: str,
        industry: str,
        proposal_type: str = "general",
    ) -> None:
        self.client_name = client_name
        self.industry = industry
        self.proposal_type = proposal_type

        self._orien: OrienData | None = None
        self._transcript: TranscriptData | None = None
        self._reference_text: str = ""
        self._extra: dict[str, Any] = {}

    # ----- Intake methods ---------------------------------------------------

    def add_orien_text(self, text: str) -> None:
        """Parse raw orientation text."""
        self._orien = parse_orien_text(text)

    def add_orien_file(self, filepath: str) -> None:
        """Parse orientation from a file."""
        self._orien = parse_orien_file(filepath)

    def add_orien_gdoc(self, url_or_id: str) -> None:
        """Read orientation from Google Docs."""
        from .gdocs_reader import read_google_doc

        text = read_google_doc(url_or_id)
        self._orien = parse_orien_text(text)

    def add_transcript_text(self, text: str) -> None:
        """Parse a meeting transcript."""
        self._transcript = parse_transcript(text)

    def add_reference_text(self, text: str) -> None:
        """Add reference proposal text."""
        self._reference_text = text

    def add_extra(self, key: str, value: Any) -> None:
        """Attach arbitrary extra context."""
        self._extra[key] = value

    # ----- Assembly ---------------------------------------------------------

    def assemble(self) -> dict[str, Any]:
        """Produce the unified context dictionary.

        Returns
        -------
        dict
            Keys: client_name, industry, proposal_type, orien, transcript,
            reference_text, extra, raw_orien_text.
        """
        orien_dict: dict[str, Any] = {}
        raw_orien = ""
        if self._orien:
            orien_dict = asdict(self._orien)
            raw_orien = self._orien.raw_text
            # Override client name if parsed from notes, else use CLI arg
            if self._orien.client_name:
                orien_dict["client_name"] = self._orien.client_name

        transcript_dict: dict[str, Any] = {}
        if self._transcript:
            transcript_dict = asdict(self._transcript)

        ctx = {
            "client_name": self.client_name,
            "industry": self.industry,
            "proposal_type": self.proposal_type,
            "orien": orien_dict,
            "transcript": transcript_dict,
            "reference_text": self._reference_text,
            "extra": self._extra,
            "raw_orien_text": raw_orien,
        }

        logger.info(
            "Context assembled: client=%s, industry=%s, type=%s, "
            "orien=%s, transcript=%s",
            self.client_name,
            self.industry,
            self.proposal_type,
            bool(self._orien),
            bool(self._transcript),
        )
        return ctx
