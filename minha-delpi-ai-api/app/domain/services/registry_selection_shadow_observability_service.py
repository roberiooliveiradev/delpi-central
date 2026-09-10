"""Telemetria E1.S4 — shadow markers/intent vs retrieval (sem alterar seleção)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class RegistrySelectionShadowObservabilityService:
    """Emite métricas estruturadas de agree/diverge do selection shadow."""

    @classmethod
    def record(cls, shadow: dict[str, Any] | None) -> None:
        if not isinstance(shadow, dict):
            return
        logger.info(
            "registry_selection_shadow",
            extra={
                "metric": "registry_selection_shadow",
                "kind": str(shadow.get("kind") or "registry_route_id"),
                "routeId": str(shadow.get("routeId") or ""),
                "legacyActionId": str(shadow.get("legacyActionId") or ""),
                "agree": bool(shadow.get("agree")),
                "candidateTopCount": len(shadow.get("candidateTopIds") or []),
                "error": str(shadow.get("error") or "") or None,
            },
        )
