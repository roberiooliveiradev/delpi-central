"""Catálogo TV Dashboard — fetch/cache versionado + suggest-ops (sem ops embutidas)."""

from __future__ import annotations

from typing import Any

from app.domain.ports.tv_dashboard_capability_catalog_port import (
    TvDashboardCapabilityCatalogPort,
)

_catalog_port: TvDashboardCapabilityCatalogPort | None = None


def configure_tv_dashboard_catalog_port(port: TvDashboardCapabilityCatalogPort | None) -> None:
    global _catalog_port
    _catalog_port = port


def get_tv_dashboard_catalog_port() -> TvDashboardCapabilityCatalogPort:
    global _catalog_port
    if _catalog_port is None:
        from app.infrastructure.adapters.tv_dashboard_capability_catalog_adapter import (
            TvDashboardCapabilityCatalogAdapter,
        )

        _catalog_port = TvDashboardCapabilityCatalogAdapter()
    return _catalog_port


class ChatTvDashboardCatalogService:
    """Orquestra GET capabilities + POST suggest-ops via port injetável."""

    def __init__(self, catalog_port: TvDashboardCapabilityCatalogPort | None = None) -> None:
        self._port = catalog_port

    def _resolve_port(self) -> TvDashboardCapabilityCatalogPort:
        return self._port or get_tv_dashboard_catalog_port()

    def get_catalog(self, access_token: str | None) -> dict[str, Any] | None:
        if not access_token:
            return None
        return self._resolve_port().fetch_catalog(access_token)

    def suggest_ops(
        self,
        *,
        message: str,
        host_context: dict | None,
        access_token: str | None,
    ) -> dict[str, Any] | None:
        if not access_token:
            return None
        return self._resolve_port().suggest_ops(
            message,
            host_context,
            access_token,
        )

    @staticmethod
    def when_to_use_summaries(
        catalog: dict[str, Any] | None,
        *,
        max_items: int = 12,
        max_chars: int = 900,
    ) -> str:
        from app.domain.services.chat_tv_dashboard_copilot_intent_service import (
            ChatTvDashboardCopilotIntentService,
        )

        return ChatTvDashboardCopilotIntentService.format_catalog_when_to_use(
            catalog,
            max_items=max_items,
            max_chars=max_chars,
        )
