"""Compila spec chart/encoding/palette → chartPresentation."""

from __future__ import annotations

from typing import Any

from app.domain.entities.presentation_spec import PresentationSpec
from app.domain.services.presentation_format_mapping_service import (
    PresentationFormatMappingService,
)

# Mirror of plugin-ui ColorFamilyCatalog — prefer paletteFamily emission over colors[].
_PALETTE_TO_SERIES: dict[str, list[str]] = {
    "brand": ["var(--mdc-chart-series-1)", "var(--mdc-chart-series-10)"],
    "sequential-blue": ["var(--mdc-heatmap-low)", "var(--mdc-heatmap-high)"],
    "cool": ["var(--mdc-chart-series-7)", "var(--mdc-chart-series-2)"],
    "warm": ["var(--mdc-chart-series-4)", "var(--mdc-chart-series-5)"],
    "diverging-status": ["var(--mdc-chart-series-5)", "var(--mdc-chart-series-3)"],
    # status alias — same semantic pair as diverging-status (MFE catalog aligned)
    "status": ["var(--mdc-chart-series-5)", "var(--mdc-chart-series-3)"],
}


class PresentationChartCompilerService:
    @classmethod
    def apply(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec,
        labels: dict[str, str],
        formats: dict[str, str],
    ) -> None:
        chart = metadata.get("chartPresentation")
        if not isinstance(chart, dict) and isinstance(metadata.get("presentation"), dict):
            if metadata["presentation"].get("type") == "chart":
                chart = metadata["presentation"]
        if not isinstance(chart, dict) or chart.get("type") != "chart":
            if not (spec.view == "chart" or spec.mark):
                return
            chart = cls._materialize_chart_slot(metadata, spec=spec)
            if chart is None:
                return
            metadata["chartPresentation"] = chart

        tabular_rows = cls._prefer_table_rows(metadata)
        if tabular_rows and (
            spec.mark == "heatmap"
            or not isinstance(chart.get("data"), list)
            or len(chart.get("data") or []) < len(tabular_rows)
        ):
            chart["data"] = tabular_rows

        config = dict(chart.get("config") or {})
        x = spec.encoding.get("x")
        y = spec.encoding.get("y")
        color = spec.encoding.get("color")

        if x:
            config["xAxis"] = x.field
        if y and spec.mark != "heatmap":
            config["yAxis"] = y.field
        if spec.mark == "heatmap":
            if x:
                config["xAxis"] = x.field
            if y:
                config["yAxis"] = y.field
            if color:
                config["valueKey"] = color.field
        elif color and not y:
            config["yAxis"] = color.field

        if spec.mark:
            chart["chartType"] = spec.mark

        field_labels = dict(config.get("fieldLabels") or {})
        field_labels.update(labels)
        config["fieldLabels"] = field_labels

        field_formats = dict(config.get("fieldFormats") or {})
        field_formats.update(
            PresentationFormatMappingService.map_chart_field_formats(formats)
        )
        config["fieldFormats"] = field_formats

        if spec.legend_visible is not None:
            config["legend"] = bool(spec.legend_visible)

        palette = spec.palette_family or (
            "sequential-blue" if spec.mark == "heatmap" else None
        )
        if palette:
            config["paletteFamily"] = palette
            config["colors"] = list(
                _PALETTE_TO_SERIES.get(palette) or _PALETTE_TO_SERIES["brand"]
            )

        config["bindingProvenance"] = "COMPILED"
        chart["config"] = config

        metadata["chartPresentation"] = chart
        if metadata.get("presentation") is chart or (
            isinstance(metadata.get("presentation"), dict)
            and metadata["presentation"].get("type") == "chart"
        ):
            metadata["presentation"] = chart

    @classmethod
    def _prefer_table_rows(cls, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("tablePresentation",):
            presentation = metadata.get(key)
            if isinstance(presentation, dict) and presentation.get("type") == "table":
                rows = presentation.get("rows")
                if isinstance(rows, list):
                    typed = [row for row in rows if isinstance(row, dict)]
                    if typed:
                        return typed
        tables = metadata.get("tablePresentations")
        if isinstance(tables, list) and tables and isinstance(tables[0], dict):
            rows = tables[0].get("rows")
            if isinstance(rows, list):
                typed = [row for row in rows if isinstance(row, dict)]
                if typed:
                    return typed
        return []

    @classmethod
    def _materialize_chart_slot(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec,
    ) -> dict[str, Any] | None:
        if not spec.encoding:
            return None
        rows = cls._prefer_table_rows(metadata) or cls._tabular_rows(metadata)
        if not rows:
            return None
        return {
            "type": "chart",
            "title": "",
            "chartType": spec.mark or "bar",
            "data": rows,
            "config": {},
        }

    @classmethod
    def _tabular_rows(cls, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        preferred = cls._prefer_table_rows(metadata)
        if preferred:
            return preferred
        for key in ("presentation", "chartPresentation"):
            presentation = metadata.get(key)
            if not isinstance(presentation, dict):
                continue
            if presentation.get("type") == "table":
                rows = presentation.get("rows")
                if isinstance(rows, list):
                    return [row for row in rows if isinstance(row, dict)]
            if presentation.get("type") == "chart":
                data = presentation.get("data")
                if isinstance(data, list):
                    return [row for row in data if isinstance(row, dict)]
        return []
