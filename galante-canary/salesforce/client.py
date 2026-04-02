"""Salesforce connection — lazy import of simple_salesforce."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from config import SF_DOMAIN, SF_PASSWORD, SF_SECURITY_TOKEN, SF_USERNAME

if TYPE_CHECKING:
    from simple_salesforce import Salesforce

logger = logging.getLogger(__name__)

_sf_instance: Salesforce | None = None


def get_client() -> Salesforce:
    """Return a cached Salesforce client (lazy-imported)."""
    global _sf_instance
    if _sf_instance is not None:
        return _sf_instance

    try:
        from simple_salesforce import Salesforce  # noqa: WPS433
    except ImportError as exc:
        raise RuntimeError(
            "simple-salesforce がインストールされていません。"
            "  pip install simple-salesforce  を実行してください。"
        ) from exc

    if not all([SF_USERNAME, SF_PASSWORD, SF_SECURITY_TOKEN]):
        raise RuntimeError(
            "Salesforce 認証情報が設定されていません。"
            " .env ファイルに SF_USERNAME / SF_PASSWORD / SF_SECURITY_TOKEN を設定してください。"
        )

    logger.info("Salesforce に接続中...")
    _sf_instance = Salesforce(
        username=SF_USERNAME,
        password=SF_PASSWORD,
        security_token=SF_SECURITY_TOKEN,
        domain=SF_DOMAIN,
    )
    logger.info("Salesforce 接続完了")
    return _sf_instance
