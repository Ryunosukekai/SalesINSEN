"""Salesforce接続クライアント（lazy import）."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from simple_salesforce import Salesforce

from config import SalesforceConfig

logger = logging.getLogger(__name__)


class SalesforceClient:
    """Salesforce REST API クライアント.

    simple_salesforce は connect() 時に初めて import される。
    デモモードでは一切 import されない。
    """

    def __init__(self, sf_config: SalesforceConfig) -> None:
        self._config = sf_config
        self._sf: Optional[Salesforce] = None

    # ------------------------------------------------------------------
    # 接続
    # ------------------------------------------------------------------
    def connect(self) -> None:
        """Salesforce に接続する（lazy import）."""
        from simple_salesforce import Salesforce  # noqa: WPS433

        logger.info("Salesforce に接続中 (domain=%s) ...", self._config.domain)
        self._sf = Salesforce(
            username=self._config.username,
            password=self._config.password,
            security_token=self._config.security_token,
            domain=self._config.domain,
            version=self._config.api_version,
        )
        logger.info("Salesforce 接続成功")

    @property
    def sf(self) -> Salesforce:
        """接続済みインスタンスを返す。未接続なら自動接続."""
        if self._sf is None:
            self.connect()
        assert self._sf is not None
        return self._sf

    # ------------------------------------------------------------------
    # クエリ実行
    # ------------------------------------------------------------------
    def query(self, soql: str) -> list[dict[str, Any]]:
        """SOQL を実行し、レコード一覧を返す."""
        logger.debug("SOQL: %s", soql[:200])
        result = self.sf.query_all(soql)
        records: list[dict[str, Any]] = result.get("records", [])
        logger.info("取得レコード数: %d", len(records))
        return records
