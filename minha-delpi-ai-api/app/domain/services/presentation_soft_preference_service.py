"""Soft preferences Draco-lite — completa Spec sem violar hard constraints."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from app.domain.entities.presentation_data_profile import PresentationDataProfile
from app.domain.entities.presentation_spec import (
    SUPPORTED_MARKS,
    SUPPORTED_PALETTE_FAMILIES,
    PresentationSpec,
)
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "presentation_composer_soft_preferences"


class PresentationSoftPreferenceService:
    """Aplica preferências suaves após binder/composer; nunca sobrescreve hard bindings."""

    @classmethod
    def apply(
        cls,
        spec: PresentationSpec | None,
        *,
        profile: PresentationDataProfile | None = None,
    ) -> PresentationSpec | None:
        if spec is None:
            return None

        defaults = ChatAssistantContentService.get_node(_BUNDLE, "defaults")
        if not isinstance(defaults, dict):
            defaults = {}

        updated = spec

        if updated.mark == "heatmap":
            if not updated.palette_family:
                family = str(defaults.get("heatmapPaletteFamily") or "sequential-blue")
                if family in SUPPORTED_PALETTE_FAMILIES:
                    updated = replace(updated, palette_family=family)
            if updated.legend_visible is None:
                updated = replace(
                    updated,
                    legend_visible=bool(defaults.get("heatmapLegendVisible", False)),
                )
        elif updated.view == "chart" or updated.mark:
            if not updated.palette_family:
                family = str(defaults.get("categoricalPaletteFamily") or "brand")
                if family in SUPPORTED_PALETTE_FAMILIES:
                    updated = replace(updated, palette_family=family)
            if updated.legend_visible is None and updated.mark not in {None, "heatmap"}:
                updated = replace(
                    updated,
                    legend_visible=bool(defaults.get("chartLegendVisible", True)),
                )
            if not updated.mark and updated.view == "chart":
                mark = str(defaults.get("defaultChartMark") or "bar")
                if mark in SUPPORTED_MARKS:
                    updated = replace(updated, mark=mark)

        if updated.view == "table" and updated.fields and profile is not None:
            weights = ChatAssistantContentService.get_node(_BUNDLE, "weights")
            cap = 8
            if isinstance(weights, dict):
                try:
                    cap = max(1, int(weights.get("preferFewerTableFieldsCap") or 8))
                except (TypeError, ValueError):
                    cap = 8
            # Soft: only trim when fields were auto-filled (no explicit short list).
            if len(updated.fields) > cap and updated.provenance == "DETERMINISTIC":
                known = {item.key for item in profile.fields}
                trimmed = tuple(key for key in updated.fields if key in known)[:cap]
                if trimmed:
                    updated = replace(updated, fields=trimmed)

        return updated

    @classmethod
    def score(cls, spec: PresentationSpec) -> float:
        """Ranking score for unit tests — higher is better; soft only."""
        weights = ChatAssistantContentService.get_node(_BUNDLE, "weights")
        if not isinstance(weights, dict):
            weights = {}
        score = 0.0
        if spec.mark == "heatmap":
            if spec.palette_family == "sequential-blue":
                score += float(weights.get("preferSequentialBlueForHeatmap") or 0)
            if spec.legend_visible is False:
                score += float(weights.get("preferLegendHiddenForHeatmap") or 0)
        elif spec.view == "chart" or spec.mark:
            if spec.palette_family == "brand":
                score += float(weights.get("preferBrandForCategoricalChart") or 0)
            if spec.mark == "bar" and "x" in spec.encoding and "y" in spec.encoding:
                score += float(weights.get("preferBarWhenNominalXQuantitativeY") or 0)
            if spec.legend_visible is True:
                score += float(weights.get("preferLegendVisibleForMultiSeries") or 0)
        return score
