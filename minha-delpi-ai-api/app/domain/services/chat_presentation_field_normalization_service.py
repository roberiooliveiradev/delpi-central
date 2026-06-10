"""Normaliza labels e formatos de campos em apresentações ricas (tabela, gráfico, dashboard)."""

from __future__ import annotations

from typing import Any

from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)


class ChatPresentationFieldNormalizationService:
    """Aplica vocabulário central (`column_labels.json`) a qualquer presentation da tool."""

    _column_labels = ExternalActionColumnLabelService()

    @classmethod
    def normalize_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        path: str = "",
        schema_labels: dict[str, str] | None = None,
        schema_formats: dict[str, str] | None = None,
    ) -> None:
        if not isinstance(metadata, dict):
            return

        for key in (
            "presentation",
            "tablePresentation",
            "chartPresentation",
            "treePresentation",
            "kpiPresentation",
            "dashboardPresentation",
            "profileTablePresentation",
            "inspectionTablePresentation",
        ):
            presentation = metadata.get(key)

            if isinstance(presentation, dict):
                metadata[key] = cls.normalize_presentation(
                    presentation,
                    path=path,
                    schema_labels=schema_labels,
                    schema_formats=schema_formats,
                )

        table_presentations = metadata.get("tablePresentations")

        if isinstance(table_presentations, list):
            metadata["tablePresentations"] = [
                cls.normalize_presentation(
                    presentation,
                    path=path,
                    schema_labels=schema_labels,
                    schema_formats=schema_formats,
                )
                for presentation in table_presentations
                if isinstance(presentation, dict)
            ]

    @classmethod
    def normalize_presentation(
        cls,
        presentation: dict[str, Any],
        *,
        path: str = "",
        schema_labels: dict[str, str] | None = None,
        schema_formats: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(presentation, dict):
            return presentation

        presentation_type = str(presentation.get("type") or "").strip().lower()

        if presentation_type == "table":
            return cls._normalize_table(
                presentation,
                path=path,
                schema_labels=schema_labels,
                schema_formats=schema_formats,
            )

        if presentation_type == "chart":
            return cls._normalize_chart(
                presentation,
                schema_labels=schema_labels,
                schema_formats=schema_formats,
            )

        if presentation_type == "dashboard":
            return cls._normalize_dashboard(
                presentation,
                path=path,
                schema_labels=schema_labels,
                schema_formats=schema_formats,
            )

        return presentation

    @classmethod
    def _normalize_table(
        cls,
        presentation: dict[str, Any],
        *,
        path: str,
        schema_labels: dict[str, str] | None,
        schema_formats: dict[str, str] | None,
    ) -> dict[str, Any]:
        rows = presentation.get("rows") or []
        first_row = next((row for row in rows if isinstance(row, dict)), None)
        columns = presentation.get("columns") or []

        if first_row:
            profile_name = cls._column_labels.detect_table_profile(first_row, path=path)
            preferred = None

            if profile_name:
                preferred = cls._column_labels.preferred_columns(
                    profile_name,
                    first_row,
                    schema_labels=schema_labels,
                )

            if preferred:
                columns = [
                    cls._column_labels.enrich_column_def(
                        key,
                        label=label,
                        schema_labels=schema_labels,
                        schema_formats=schema_formats,
                    )
                    for key, label in preferred
                ]
            elif not columns:
                columns = [
                    cls._column_labels.enrich_column_def(
                        key,
                        schema_labels=schema_labels,
                        schema_formats=schema_formats,
                    )
                    for key in list(first_row.keys())[:15]
                    if not isinstance(first_row.get(key), (list, dict))
                ]

        normalized_columns: list[dict[str, str]] = []

        for column in columns:
            if not isinstance(column, dict):
                continue

            key = str(column.get("key") or "").strip()

            if not key:
                continue

            configured_label = column.get("label")
            label = (
                str(configured_label).strip()
                if isinstance(configured_label, str) and configured_label.strip()
                else None
            )
            normalized_columns.append(
                cls._column_labels.enrich_column_def(
                    key,
                    label=label,
                    schema_labels=schema_labels,
                    schema_formats=schema_formats,
                )
            )

        presentation["columns"] = normalized_columns

        if normalized_columns and rows:
            column_keys = {column["key"] for column in normalized_columns}
            presentation["rows"] = [
                {key: row.get(key) for key in column_keys}
                for row in rows
                if isinstance(row, dict)
            ]

        return presentation

    @classmethod
    def _normalize_chart(
        cls,
        presentation: dict[str, Any],
        *,
        schema_labels: dict[str, str] | None,
        schema_formats: dict[str, str] | None,
    ) -> dict[str, Any]:
        config = dict(presentation.get("config") or {})
        field_labels = dict(config.get("fieldLabels") or {})
        field_formats = dict(config.get("fieldFormats") or {})
        keys = cls._collect_chart_field_keys(presentation, config)

        for key in sorted(keys):
            if not key:
                continue

            if key not in field_labels:
                field_labels[key] = cls._column_labels.label_for(
                    key,
                    schema_labels=schema_labels,
                )

            field_format = cls._column_labels.resolve_field_format(
                key,
                schema_formats=schema_formats,
            )

            if field_format and key not in field_formats:
                field_formats[key] = field_format

        config["fieldLabels"] = field_labels

        if field_formats:
            config["fieldFormats"] = field_formats

        presentation["config"] = config
        return presentation

    @classmethod
    def _normalize_dashboard(
        cls,
        presentation: dict[str, Any],
        *,
        path: str,
        schema_labels: dict[str, str] | None,
        schema_formats: dict[str, str] | None,
    ) -> dict[str, Any]:
        panels = presentation.get("panels")

        if not isinstance(panels, list):
            return presentation

        presentation["panels"] = [
            {
                **panel,
                "presentation": cls.normalize_presentation(
                    panel.get("presentation") or {},
                    path=path,
                    schema_labels=schema_labels,
                    schema_formats=schema_formats,
                ),
            }
            if isinstance(panel, dict)
            else panel
            for panel in panels
        ]

        return presentation

    @classmethod
    def _collect_chart_field_keys(
        cls,
        presentation: dict[str, Any],
        config: dict[str, Any],
    ) -> set[str]:
        keys: set[str] = set()

        for axis_key in (
            config.get("xAxis"),
            config.get("valueKey"),
            config.get("comboBarKey"),
            config.get("comboLineKey"),
            config.get("gaugeValueKey"),
            config.get("gaugeTargetKey"),
        ):
            if isinstance(axis_key, str) and axis_key.strip():
                keys.add(axis_key.strip())

        y_axis = config.get("yAxis")

        if isinstance(y_axis, str) and y_axis.strip():
            keys.add(y_axis.strip())
        elif isinstance(y_axis, list):
            keys.update(
                str(item).strip()
                for item in y_axis
                if isinstance(item, str) and item.strip()
            )

        for list_key in ("numericColumns", "categoryColumns"):
            configured = config.get(list_key)

            if isinstance(configured, list):
                keys.update(
                    str(item).strip()
                    for item in configured
                    if isinstance(item, str) and item.strip()
                )

        for row in presentation.get("data") or []:
            if isinstance(row, dict):
                keys.update(str(key).strip() for key in row.keys() if str(key).strip())

        return keys
