"""Compila PresentationSpec validado → slots chart/table + presentationDecision enrichment."""

from __future__ import annotations

from typing import Any

from app.domain.entities.presentation_data_profile import PresentationDataProfile
from app.domain.entities.presentation_spec import PresentationSpec

_PALETTE_TO_SERIES: dict[str, list[str]] = {
    "brand": ["var(--mdc-chart-series-1)", "var(--mdc-chart-series-10)"],
    "sequential-blue": ["var(--mdc-heatmap-low)", "var(--mdc-heatmap-high)"],
    "cool": ["var(--mdc-chart-series-7)", "var(--mdc-chart-series-2)"],
    "warm": ["var(--mdc-chart-series-4)", "var(--mdc-chart-series-5)"],
    "diverging-status": ["var(--mdc-chart-series-5)", "var(--mdc-chart-series-3)"],
    "status": ["var(--mdc-chart-series-3)", "var(--mdc-chart-series-5)"],
}


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
        chart = metadata.get("chartPresentation")
        if not isinstance(chart, dict) and isinstance(metadata.get("presentation"), dict):
            if metadata["presentation"].get("type") == "chart":
                chart = metadata["presentation"]
        if not isinstance(chart, dict) or chart.get("type") != "chart":
            if not (spec.view == "chart" or spec.mark):
                return
            # Format refinement / table-first turns: materialize chart from tabular rows
            # so selected heatmap|chart is deliverable (not decision-only).
            chart = cls._materialize_chart_slot(metadata, spec=spec)
            if chart is None:
                return
            metadata["chartPresentation"] = chart

        # Heatmap / chart rebinding must not keep a prior aggregated 1-row chart slot
        # when the table still holds the full matrix.
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
            elif y and y.field:
                # fallback if color missing but y was measure (should be rare)
                pass
        elif color and not y:
            config["yAxis"] = color.field

        if spec.mark:
            chart["chartType"] = spec.mark

        field_labels = dict(config.get("fieldLabels") or {})
        field_labels.update(labels)
        config["fieldLabels"] = field_labels

        field_formats = dict(config.get("fieldFormats") or {})
        field_formats.update(formats)
        config["fieldFormats"] = field_formats

        if spec.legend_visible is not None:
            config["legend"] = bool(spec.legend_visible)

        palette = spec.palette_family or (
            "sequential-blue" if spec.mark == "heatmap" else None
        )
        if palette:
            config["paletteFamily"] = palette
            config["colors"] = list(_PALETTE_TO_SERIES.get(palette) or _PALETTE_TO_SERIES["brand"])

        config["bindingProvenance"] = "COMPILED"
        chart["config"] = config

        # Canonical slot for chart delivery (even when we rebound `presentation`).
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

    @classmethod
    def _apply_table(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec,
        labels: dict[str, str],
        formats: dict[str, str],
    ) -> None:
        tables: list[dict[str, Any]] = []
        for key in ("tablePresentation", "presentation"):
            value = metadata.get(key)
            if isinstance(value, dict) and value.get("type") == "table":
                tables.append(value)
        multi = metadata.get("tablePresentations")
        if isinstance(multi, list):
            tables.extend(item for item in multi if isinstance(item, dict))

        preferred = list(spec.fields) if spec.fields else None
        for table in tables:
            columns = table.get("columns")
            if not isinstance(columns, list):
                continue
            normalized: list[dict[str, Any]] = []
            for column in columns:
                if not isinstance(column, dict):
                    continue
                key = str(column.get("key") or "").strip()
                if not key:
                    continue
                if preferred and key not in preferred:
                    continue
                label = labels.get(key) or str(column.get("label") or key)
                entry = dict(column)
                entry["key"] = key
                entry["label"] = label
                if formats.get(key) and not entry.get("dataType"):
                    entry["dataType"] = formats[key]
                normalized.append(entry)
            if preferred:
                order = {key: index for index, key in enumerate(preferred)}
                normalized.sort(key=lambda item: order.get(str(item.get("key")), 10_000))
            if normalized:
                table["columns"] = normalized

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
