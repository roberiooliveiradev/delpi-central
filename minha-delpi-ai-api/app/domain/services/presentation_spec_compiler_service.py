"""Compila PresentationSpec validado → slots chart/table + presentationDecision enrichment."""

from __future__ import annotations

from typing import Any

from app.domain.entities.presentation_data_profile import PresentationDataProfile
from app.domain.entities.presentation_spec import PresentationSpec
from app.domain.services.presentation_compilers.presentation_chart_compiler_service import (
    PresentationChartCompilerService,
)
from app.domain.services.presentation_compilers.presentation_dashboard_compiler_service import (
    PresentationDashboardCompilerService,
)
from app.domain.services.presentation_compilers.presentation_delivery_compiler_service import (
    PresentationDeliveryCompilerService,
)
from app.domain.services.presentation_compilers.presentation_kpi_compiler_service import (
    PresentationKpiCompilerService,
)
from app.domain.services.presentation_compilers.presentation_table_compiler_service import (
    PresentationTableCompilerService,
)
from app.domain.services.presentation_compilers.presentation_text_compiler_service import (
    PresentationTextCompilerService,
)
from app.domain.services.presentation_compilers.presentation_tree_compiler_service import (
    PresentationTreeCompilerService,
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
        cls._apply_kpi(
            metadata,
            spec=spec,
            profile=profile,
            labels=labels,
            formats=formats,
        )
        cls._apply_tree(
            metadata,
            spec=spec,
            profile=profile,
            labels=labels,
        )
        cls._apply_dashboard(metadata, spec=spec)
        cls._apply_text(metadata, spec=spec)
        PresentationDeliveryCompilerService.apply(metadata, spec=spec)

        metadata["presentationSpec"] = spec.as_dict()
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
    def _apply_kpi(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec,
        profile: PresentationDataProfile,
        labels: dict[str, str],
        formats: dict[str, str],
    ) -> None:
        PresentationKpiCompilerService.apply(
            metadata,
            spec=spec,
            profile=profile,
            labels=labels,
            formats=formats,
        )

    @classmethod
    def _apply_tree(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec,
        profile: PresentationDataProfile,
        labels: dict[str, str],
    ) -> None:
        PresentationTreeCompilerService.apply(
            metadata,
            spec=spec,
            profile=profile,
            labels=labels,
        )

    @classmethod
    def _apply_dashboard(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec,
    ) -> None:
        PresentationDashboardCompilerService.apply(metadata, spec=spec)

    @classmethod
    def _apply_text(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec,
    ) -> None:
        PresentationTextCompilerService.apply(metadata, spec=spec)
