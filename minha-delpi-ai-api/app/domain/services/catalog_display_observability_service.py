"""Telemetria de display catalogs → OpenAPI (hit rates / shadow diffs)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class CatalogDisplayObservabilityService:
    """Emite métricas estruturadas sem alterar routing."""

    @classmethod
    def record_action_label(
        cls,
        *,
        source: str,
        path: str = "",
        provider_key: str = "",
        shadow_diff: bool = False,
    ) -> None:
        logger.info(
            "catalog_display_action_label",
            extra={
                "metric": "action_display_label_source",
                "source": source,
                "path": path,
                "providerKey": provider_key,
                "shadowDiff": shadow_diff,
                "manualCatalogHit": source == "LEGACY_PATH_LABEL",
            },
        )

    @classmethod
    def record_presentation_title(
        cls,
        *,
        source: str,
        path: str = "",
        shadow_diff: bool = False,
    ) -> None:
        logger.info(
            "catalog_display_presentation_title",
            extra={
                "metric": "presentation_title_source",
                "source": source,
                "path": path,
                "shadowDiff": shadow_diff,
                "pathCoupled": source.startswith("LEGACY"),
            },
        )

    @classmethod
    def snapshot_counters(cls, event: dict[str, Any]) -> dict[str, Any]:
        """Normaliza contadores para evals R8/R11 (sem I/O)."""
        return {
            "manual_catalog_hit_rate": float(event.get("manualCatalogHitRate") or 0.0),
            "path_coupled_display_rules_remaining": int(
                event.get("pathCoupledRulesRemaining") or 0
            ),
            "llm_calls_per_turn": float(event.get("llmCallsPerTurn") or 0.0),
            "technical_label_leak_rate": float(event.get("technicalLabelLeakRate") or 0.0),
            "presentation_title_consistency_rate": float(
                event.get("presentationTitleConsistencyRate") or 1.0
            ),
        }
