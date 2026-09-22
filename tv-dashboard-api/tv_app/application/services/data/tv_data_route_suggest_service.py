"""BFF: NL → sugestões de fontes do catálogo TV (discovery owner-local)."""

from __future__ import annotations

from typing import Any

from tv_app.application.services.data.tv_data_route_discovery_service import (
    TvDataRouteDiscoveryService,
)
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


class TvDataRouteSuggestService:
    """Thin façade over ``TvDataRouteDiscoveryService`` (no Chat AI authority)."""

    def __init__(
        self,
        catalog: TvDataRouteCatalogService,
        *,
        discovery: TvDataRouteDiscoveryService | None = None,
        ai_client: Any = None,  # retained for call-site compat; ignored
    ) -> None:
        self._catalog = catalog
        self._discovery = discovery or TvDataRouteDiscoveryService(catalog)

    def suggest(
        self,
        *,
        query: str,
        limit: int = 5,
        category: str | None = None,
    ) -> dict[str, Any]:
        return self._discovery.discover(
            query=query,
            limit=limit,
            category=category,
        )
