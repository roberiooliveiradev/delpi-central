"""Compila spec.kpi.measureFields → kpiPresentation cards (agregação determinística)."""

from __future__ import annotations

from typing import Any

from app.domain.entities.presentation_data_profile import PresentationDataProfile
from app.domain.entities.presentation_spec import PresentationSpec
from app.domain.services.chat_presentation_kpi_assembly_service import (
    ChatPresentationKpiAssemblyService,
)
from app.domain.services.presentation_compilers.presentation_chart_compiler_service import (
    PresentationChartCompilerService,
)
from app.domain.services.presentation_format_mapping_service import (
    PresentationFormatMappingService,
)

_MAX_KPI_CARDS = 8

_TONE_TO_COLOR: dict[str, str] = {
    "brand": "var(--mdc-chart-series-1)",
    "primary": "var(--mdc-chart-series-1)",
    "success": "var(--mdc-chart-series-3)",
    "positive": "var(--mdc-chart-series-3)",
    "warning": "var(--mdc-chart-series-5)",
    "danger": "var(--mdc-chart-series-5)",
    "info": "var(--mdc-chart-series-2)",
    "neutral": "var(--mdc-chart-series-7)",
    "cool": "var(--mdc-chart-series-7)",
    "warm": "var(--mdc-chart-series-4)",
}


class PresentationKpiCompilerService:
    @classmethod
    def apply(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec,
        profile: PresentationDataProfile,
        labels: dict[str, str],
        formats: dict[str, str],
    ) -> None:
        kpi = metadata.get("kpiPresentation")
        if not isinstance(kpi, dict) and isinstance(metadata.get("presentation"), dict):
            if metadata["presentation"].get("type") == "kpi":
                kpi = metadata["presentation"]

        if isinstance(kpi, dict):
            cards = kpi.get("cards")
            if isinstance(cards, list):
                for card in cards:
                    if not isinstance(card, dict):
                        continue
                    key = str(card.get("key") or card.get("id") or "").strip()
                    if key and labels.get(key):
                        card["label"] = labels[key]
                    elif not str(card.get("label") or "").strip() and key:
                        card["label"] = labels.get(key, key)

        if spec.kpi is None or not spec.kpi.measure_fields:
            return

        rows = cls._tabular_rows(metadata)
        if not rows:
            return

        if not isinstance(kpi, dict):
            kpi = {"type": "kpi", "title": "Indicadores", "cards": []}
            metadata["kpiPresentation"] = kpi

        measure_order = cls._resolve_measure_order(spec)
        tones = list(spec.kpi.tones or ())
        audit_entries: list[dict[str, Any]] = []
        compiled_cards: list[dict[str, Any]] = []

        for index, field_key in enumerate(measure_order[:_MAX_KPI_CARDS]):
            aggregated = cls._aggregate_field(rows, field_key, profile=profile)
            if aggregated is None:
                continue

            tone = tones[index] if index < len(tones) else None
            color = _TONE_TO_COLOR.get(str(tone or "").strip().lower()) if tone else None
            label = labels.get(field_key) or field_key
            data_type = PresentationFormatMappingService.to_mfe_data_type(
                formats.get(field_key)
            )

            card: dict[str, Any] = {
                "key": field_key,
                "label": label,
                "value": aggregated["value"],
            }
            if color:
                card["color"] = color
            if tone:
                card["tone"] = tone
            if data_type:
                card["dataType"] = data_type

            compiled_cards.append(
                ChatPresentationKpiAssemblyService.normalize_card(card)
            )
            audit_entries.append(
                {
                    "field": field_key,
                    "aggregation": aggregated["aggregation"],
                    "rowCount": aggregated["rowCount"],
                    "nonNullCount": aggregated["nonNullCount"],
                }
            )

        if not compiled_cards:
            return

        kpi["cards"] = compiled_cards[:_MAX_KPI_CARDS]
        intelligence = metadata.setdefault("presentationIntelligence", {})
        if isinstance(intelligence, dict):
            intelligence["kpiAudit"] = audit_entries

        if metadata.get("presentation") is kpi or (
            isinstance(metadata.get("presentation"), dict)
            and metadata["presentation"].get("type") == "kpi"
        ):
            metadata["presentation"] = kpi

    @classmethod
    def _resolve_measure_order(cls, spec: PresentationSpec) -> list[str]:
        if spec.kpi is None:
            return []
        if spec.kpi.card_order:
            ordered = [key for key in spec.kpi.card_order if key in spec.kpi.measure_fields]
            remaining = [key for key in spec.kpi.measure_fields if key not in ordered]
            return ordered + remaining
        return list(spec.kpi.measure_fields)

    @classmethod
    def _tabular_rows(cls, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        return PresentationChartCompilerService._prefer_table_rows(metadata) or (
            PresentationChartCompilerService._tabular_rows(metadata)
        )

    @classmethod
    def _aggregate_field(
        cls,
        rows: list[dict[str, Any]],
        field_key: str,
        *,
        profile: PresentationDataProfile,
    ) -> dict[str, Any] | None:
        values: list[Any] = []
        for row in rows:
            if field_key not in row:
                continue
            value = row.get(field_key)
            if value is None or value == "":
                continue
            values.append(value)

        if not values:
            return None

        field_profile = profile.field_map().get(field_key)
        numeric_values: list[float] = []
        for value in values:
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                numeric_values.append(float(value))
                continue
            try:
                numeric_values.append(float(value))
            except (TypeError, ValueError):
                continue

        if numeric_values and (
            field_profile is None
            or field_profile.is_measure_candidate
            or field_profile.semantic_type == "quantitative"
        ):
            return {
                "value": round(sum(numeric_values), 4),
                "aggregation": "sum",
                "rowCount": len(rows),
                "nonNullCount": len(numeric_values),
            }

        return {
            "value": len(values),
            "aggregation": "count",
            "rowCount": len(rows),
            "nonNullCount": len(values),
        }
