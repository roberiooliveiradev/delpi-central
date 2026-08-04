"""Adapter HTTP do catálogo TV — cache por catalogVersion; sem ops embutidas."""

from __future__ import annotations

import logging
from typing import Any

from app.domain.ports.tv_dashboard_capability_catalog_port import (
    TvDashboardCapabilityCatalogPort,
)
from app.infrastructure.gateways.tv_dashboard_api_gateway import TvDashboardApiGateway

logger = logging.getLogger(__name__)


class TvDashboardCapabilityCatalogAdapter(TvDashboardCapabilityCatalogPort):
    def __init__(self, gateway: TvDashboardApiGateway | None = None) -> None:
        self._gateway = gateway or TvDashboardApiGateway()
        self._cached_version: str | None = None
        self._cached_catalog: dict[str, Any] | None = None

    def fetch_catalog(self, access_token: str) -> dict[str, Any] | None:
        if not access_token:
            return None
        try:
            payload = self._gateway.get_capabilities(access_token)
        except Exception:
            logger.warning("tv_copilot_capabilities_fetch_failed", exc_info=True)
            return None

        if not payload.get("_ok"):
            logger.warning(
                "tv_copilot_capabilities_http_error status=%s",
                payload.get("_httpStatus"),
            )
            return None

        document = self._unwrap_data(payload)
        if not document:
            return None

        version = str(document.get("catalogVersion") or "").strip()
        if not version:
            logger.warning("tv_copilot_capabilities_missing_catalog_version")
            return None

        if self._cached_version == version and isinstance(self._cached_catalog, dict):
            return dict(self._cached_catalog)

        if self._cached_version and self._cached_version != version:
            logger.info(
                "tv_copilot_catalog_version_skew previous=%s next=%s",
                self._cached_version,
                version,
            )

        self._cached_version = version
        self._cached_catalog = dict(document)
        return dict(self._cached_catalog)

    def suggest_ops(
        self,
        message: str,
        host_context: dict | None,
        access_token: str,
    ) -> dict[str, Any] | None:
        if not access_token:
            return None
        try:
            payload = self._gateway.suggest_ops(
                message=message,
                host_context=host_context,
                access_token=access_token,
            )
        except Exception:
            logger.warning("tv_copilot_suggest_ops_failed", exc_info=True)
            return None

        if not payload.get("_ok"):
            logger.warning(
                "tv_copilot_suggest_ops_http_error status=%s",
                payload.get("_httpStatus"),
            )
            return None

        return self._unwrap_data(payload)

    @staticmethod
    def _unwrap_data(payload: dict[str, Any]) -> dict[str, Any] | None:
        data = payload.get("data")
        if isinstance(data, dict):
            return data
        # Gateway already flattened edge cases — accept catalog-shaped root.
        if payload.get("catalogVersion") or payload.get("capabilities") or payload.get("ops") is not None:
            return {
                key: value
                for key, value in payload.items()
                if not str(key).startswith("_")
            }
        return None
