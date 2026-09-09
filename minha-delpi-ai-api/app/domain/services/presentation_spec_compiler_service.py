"""Compila PresentationSpec validado → slots chart/table + presentationDecision enrichment."""

from __future__ import annotations

from typing import Any

from app.domain.entities.presentation_data_profile import PresentationDataProfile
from app.domain.entities.presentation_spec import PresentationSpec
from app.domain.services.presentation_compilers.presentation_chart_compiler_service import (
    PresentationChartCompilerService,
)
from app.domain.services.presentation_compilers.presentation_table_compiler_service import (
    PresentationTableCompilerService,
)


class PresentationSpecCompilerService:
    @classmethod
    def compile_into_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec,
        profile: PresentationDataProfile,
        unmet_intent: str | None = None,
    ) -> None:
        if not isinstance(metadata, dict) or spec is None:
            return

        labels = dict(profile.resolved_field_labels.get("labels") or {})
        labels.update(spec.labels)
        formats = dict(profile.resolved_field_labels.get("formats") or {})
        formats.update(spec.formats)

        decision = metadata.get("presentationDecision")
        if not isinstance(decision, dict):
            decision = {}
            metadata["presentationDecision"] = decision

        decision["bindingProvenance"] = spec.provenance
        decision["presentationSpecApplied"] = True
        if unmet_intent:
            decision["unmetIntent"] = unmet_intent

        if spec.view and spec.view != "auto":
            selected = spec.view
            if spec.mark == "heatmap":
                selected = "heatmap"
            elif spec.mark in {"line", "multi_line"}:
                selected = "line_chart"
            elif spec.mark in {"bar", "grouped_bar", "stacked_bar"}:
                selected = "bar_chart"
            elif spec.mark == "horizontal_bar":
                selected = "horizontal_bar"
            elif spec.mark in {"donut", "pie"}:
                selected = "donut"
            decision["selected"] = selected

        cls._apply_chart(metadata, spec=spec, labels=labels, formats=formats)
        cls._apply_table(metadata, spec=spec, labels=labels, formats=formats)
        cls._apply_kpi(metadata, labels=labels)

        metadata["presentationDataProfile"] = profile.as_dict()

    @classmethod
    def _apply_chart(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec,
        labels: dict[str, str],
        formats: dict[str, str],
    ) -> None:
        PresentationChartCompilerService.apply(
            metadata,
            spec=spec,
            labels=labels,
            formats=formats,
        )

    @classmethod
    def _apply_table(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec,
        labels: dict[str, str],
        formats: dict[str, str],
    ) -> None:
        PresentationTableCompilerService.apply(
            metadata,
            spec=spec,
            labels=labels,
            formats=formats,
        )

    @classmethod
    def _apply_kpi(cls, metadata: dict[str, Any], *, labels: dict[str, str]) -> None:
        kpi = metadata.get("kpiPresentation")
        if not isinstance(kpi, dict) and isinstance(metadata.get("presentation"), dict):
            if metadata["presentation"].get("type") == "kpi":
                kpi = metadata["presentation"]
        if not isinstance(kpi, dict):
            return
        cards = kpi.get("cards")
        if not isinstance(cards, list):
            return
        for card in cards:
            if not isinstance(card, dict):
                continue
            key = str(card.get("key") or card.get("id") or "").strip()
            if key and labels.get(key):
                card["label"] = labels[key]
            elif not str(card.get("label") or "").strip() and key:
                card["label"] = labels.get(key, key)
