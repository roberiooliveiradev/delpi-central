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

        entity = cls._resolve_entity_token(metadata)
        if entity and not str(metadata.get("entity") or "").strip():
            metadata["entity"] = entity

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
                    entity=entity,
                )

        table_presentations = metadata.get("tablePresentations")

        if isinstance(table_presentations, list):
            metadata["tablePresentations"] = [
                cls.normalize_presentation(
                    presentation,
                    path=path,
                    schema_labels=schema_labels,
                    schema_formats=schema_formats,
                    entity=entity,
                )
                for presentation in table_presentations
                if isinstance(presentation, dict)
            ]

        from app.domain.services.chat_presentation_kpi_assembly_service import (
            ChatPresentationKpiAssemblyService,
        )

        ChatPresentationKpiAssemblyService.normalize_metadata(metadata)

        from app.domain.services.chat_presentation_table_role_service import (
            ChatPresentationTableRoleService,
        )

        ChatPresentationTableRoleService.enrich_metadata(
            metadata,
            path=path,
            entity=str(metadata.get("entity") or "").strip() or None,
        )

    @classmethod
    def _resolve_entity_token(cls, metadata: dict[str, Any]) -> str | None:
        entity = str(metadata.get("entity") or "").strip()
        if entity:
            return entity
        api_meta = metadata.get("apiDelpiResponseMeta")
        if isinstance(api_meta, dict):
            token = str(api_meta.get("entity") or "").strip()
            if token:
                return token
        profile = metadata.get("presentationProfile")
        if isinstance(profile, dict):
            token = str(profile.get("openapiEntity") or "").strip()
            if token:
                return token
        return None

    @classmethod
    def normalize_presentation(
        cls,
        presentation: dict[str, Any],
        *,
        path: str = "",
        schema_labels: dict[str, str] | None = None,
        schema_formats: dict[str, str] | None = None,
        entity: str | None = None,
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
                entity=entity,
            )

        if presentation_type == "chart":
            return cls._normalize_chart(
                presentation,
                path=path,
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

        if presentation_type == "kpi":
            from app.domain.services.chat_presentation_kpi_assembly_service import (
                ChatPresentationKpiAssemblyService,
            )

            return ChatPresentationKpiAssemblyService.normalize_presentation(presentation) or presentation

        return presentation

    @classmethod
    def _normalize_table(
        cls,
        presentation: dict[str, Any],
        *,
        path: str,
        schema_labels: dict[str, str] | None,
        schema_formats: dict[str, str] | None,
        entity: str | None = None,
    ) -> dict[str, Any]:
        """preferredColumns = hints de ordem/rótulo; colunas vêm do payload (não allowlist)."""
        rows = presentation.get("rows") or []
        first_row = next((row for row in rows if isinstance(row, dict)), None)
        raw_columns = presentation.get("columns") or []

        existing_label_by_key: dict[str, str] = {}
        present_keys: list[str] = []

        for column in raw_columns:
            if not isinstance(column, dict):
                continue

            key = str(column.get("key") or "").strip()

            if not key or key in present_keys:
                continue

            present_keys.append(key)
            configured_label = column.get("label")

            if isinstance(configured_label, str) and configured_label.strip():
                existing_label_by_key[key] = configured_label.strip()

        discovered_keys: list[str] = []

        if first_row:
            for raw_key in first_row.keys():
                key = str(raw_key or "").strip()

                if (
                    not key
                    or key.startswith("_")
                    or isinstance(first_row.get(raw_key), (list, dict))
                ):
                    continue

                if key not in discovered_keys:
                    discovered_keys.append(key)

        for key in discovered_keys:
            if key not in present_keys:
                present_keys.append(key)

        if not present_keys and first_row:
            present_keys = discovered_keys[:15]

        preferred_labels: dict[str, str] = {}
        profile_name: str | None = None

        if first_row and present_keys:
            from app.domain.services.chat_presentation_table_profile_inference_service import (
                ChatPresentationTableProfileInferenceService,
            )

            profile_name = ChatPresentationTableProfileInferenceService.infer_profile_name(
                path=path,
                entity=entity,
                sample_row=first_row,
                column_labels=cls._column_labels,
            )

            if profile_name:
                preferred_labels = {
                    key: label.strip()
                    for key, label in cls._column_labels.preferred_columns(
                        profile_name,
                        first_row,
                        schema_labels=schema_labels,
                    )
                    if isinstance(label, str) and label.strip()
                }

        ordered_keys = cls._column_labels.order_keys_with_preferred_hints(
            present_keys,
            profile_name=profile_name,
        )

        normalized_columns: list[dict[str, str]] = []

        for key in ordered_keys:
            label = preferred_labels.get(key) or existing_label_by_key.get(key)
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
        path: str = "",
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
                    path=path,
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
