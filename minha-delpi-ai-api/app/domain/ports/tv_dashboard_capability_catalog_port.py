"""Port: catálogo versionado + suggest-ops do BFF TV Dashboard.

A AI não embute ops de produto — só consome o dono do domínio (tv-dashboard-api).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TvDashboardCapabilityCatalogPort(ABC):
    @abstractmethod
    def fetch_catalog(self, access_token: str) -> dict[str, Any] | None:
        """GET /data/copilot/capabilities → documento versionado ou None se indisponível."""
        raise NotImplementedError

    @abstractmethod
    def suggest_ops(
        self,
        message: str,
        host_context: dict | None,
        access_token: str,
    ) -> dict[str, Any] | None:
        """POST /data/copilot/suggest-ops → {catalogVersion, ops, ...} ou None se falhar."""
        raise NotImplementedError
