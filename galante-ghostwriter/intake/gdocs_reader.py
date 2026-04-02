"""
Read Google Docs content via the Google Docs API.

Lazy-imports google client libraries so that demo mode works
without them installed.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger("galante_ghostwriter.intake.gdocs_reader")

# Google Docs URL patterns
_GDOC_URL_PATTERN = re.compile(
    r"https://docs\.google\.com/document/d/(?P<doc_id>[a-zA-Z0-9_-]+)"
)


def extract_doc_id(url_or_id: str) -> str:
    """Extract a Google Docs document ID from a URL or return as-is."""
    m = _GDOC_URL_PATTERN.search(url_or_id)
    if m:
        return m.group("doc_id")
    return url_or_id.strip()


def _build_docs_service():
    """Build and return a Google Docs API service client.

    Raises ImportError if google libraries are not installed,
    and RuntimeError if credentials are not configured.
    """
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise ImportError(
            "google-api-python-client / google-auth がインストールされていません。"
            "Google Docs 連携には `pip install google-api-python-client google-auth` が必要です。"
        ) from exc

    from config import GOOGLE_DELEGATED_USER, GOOGLE_SERVICE_ACCOUNT_JSON

    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON が設定されていません。.env を確認してください。"
        )

    scopes = ["https://www.googleapis.com/auth/documents.readonly"]
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_JSON, scopes=scopes
    )
    if GOOGLE_DELEGATED_USER:
        creds = creds.with_subject(GOOGLE_DELEGATED_USER)

    return build("docs", "v1", credentials=creds)


def _extract_text_from_body(body: dict) -> str:
    """Recursively extract plain text from a Google Docs body."""
    parts: list[str] = []

    for element in body.get("content", []):
        paragraph = element.get("paragraph")
        if paragraph:
            for pe in paragraph.get("elements", []):
                text_run = pe.get("textRun")
                if text_run:
                    parts.append(text_run.get("content", ""))
        table = element.get("table")
        if table:
            for row in table.get("tableRows", []):
                for cell in row.get("tableCells", []):
                    parts.append(_extract_text_from_body(cell))

    return "".join(parts)


def read_google_doc(url_or_id: str) -> str:
    """Read a Google Doc and return its plain-text content.

    Parameters
    ----------
    url_or_id : str
        A Google Docs URL or document ID.

    Returns
    -------
    str
        The plain-text content of the document.

    Raises
    ------
    ImportError
        If Google client libraries are not installed.
    RuntimeError
        If credentials are not configured.
    """
    doc_id = extract_doc_id(url_or_id)
    logger.info("Reading Google Doc: %s", doc_id)

    service = _build_docs_service()
    doc = service.documents().get(documentId=doc_id).execute()
    title = doc.get("title", "(Untitled)")
    body_text = _extract_text_from_body(doc.get("body", {}))

    logger.info("Read doc '%s' (%d chars)", title, len(body_text))
    return body_text
