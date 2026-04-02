"""
Write proposal output to Google Docs via the API.

Lazy-imports google client libraries. Only used when
GOOGLE_SERVICE_ACCOUNT_JSON is configured.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("galante_ghostwriter.output.gdocs_writer")


def _build_docs_service():
    """Build a Google Docs API service client with write access."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise ImportError(
            "google-api-python-client / google-auth がインストールされていません。"
        ) from exc

    from config import GOOGLE_DELEGATED_USER, GOOGLE_SERVICE_ACCOUNT_JSON

    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON が未設定です。")

    scopes = ["https://www.googleapis.com/auth/documents"]
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_JSON, scopes=scopes
    )
    if GOOGLE_DELEGATED_USER:
        creds = creds.with_subject(GOOGLE_DELEGATED_USER)

    return build("docs", "v1", credentials=creds)


def _markdown_to_docs_requests(markdown: str) -> list[dict[str, Any]]:
    """Convert Markdown to a list of Google Docs API insert requests.

    This is a simplified converter that handles:
    - # H1, ## H2, ### H3
    - **bold**, *italic*
    - - bullet points
    - > blockquotes
    - Plain text paragraphs
    """
    import re

    requests: list[dict[str, Any]] = []
    # We build requests in reverse because Google Docs API
    # inserts at an index, and inserting at index 1 sequentially
    # requires tracking the cursor position.
    cursor = 1  # Start after the initial newline

    lines = markdown.split("\n")
    for line in lines:
        stripped = line.strip()

        # Determine style
        style = "NORMAL_TEXT"
        text = stripped

        if stripped.startswith("# "):
            text = stripped[2:]
            style = "HEADING_1"
        elif stripped.startswith("## "):
            text = stripped[3:]
            style = "HEADING_2"
        elif stripped.startswith("### "):
            text = stripped[4:]
            style = "HEADING_3"
        elif stripped.startswith("- "):
            text = stripped[2:]
            # Bullet points handled via paragraph style
        elif stripped.startswith("> "):
            text = stripped[2:]
        elif stripped == "---":
            text = "━" * 40

        # Remove markdown bold/italic markers for plain insertion
        clean_text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        clean_text = re.sub(r"\*(.+?)\*", r"\1", clean_text)

        if not clean_text and not stripped:
            clean_text = ""

        insert_text = clean_text + "\n"

        # Insert text
        requests.append({
            "insertText": {
                "location": {"index": cursor},
                "text": insert_text,
            }
        })

        # Apply paragraph style
        end_index = cursor + len(insert_text)
        if style != "NORMAL_TEXT":
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": cursor, "endIndex": end_index},
                    "paragraphStyle": {"namedStyleType": style},
                    "fields": "namedStyleType",
                }
            })

        cursor = end_index

    return requests


def is_configured() -> bool:
    """Check if Google Docs output is available."""
    from config import GOOGLE_SERVICE_ACCOUNT_JSON
    return bool(GOOGLE_SERVICE_ACCOUNT_JSON)


def create_proposal_doc(
    markdown: str,
    title: str,
) -> str:
    """Create a new Google Doc from proposal Markdown.

    Parameters
    ----------
    markdown : str
        The proposal content in Markdown.
    title : str
        The document title.

    Returns
    -------
    str
        The URL of the created Google Doc.
    """
    service = _build_docs_service()

    # Create the document
    doc = service.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]
    logger.info("Created Google Doc: %s", doc_id)

    # Insert content
    requests = _markdown_to_docs_requests(markdown)
    if requests:
        service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": requests},
        ).execute()

    url = f"https://docs.google.com/document/d/{doc_id}/edit"
    logger.info("Proposal published to Google Docs: %s", url)
    return url
