"""Interpretação estruturada de dados — Playbook 13 P1 (`dataAnswer`)."""

from __future__ import annotations

from typing import Any, Callable

from app.domain.services.chat_data_anomaly_detection_service import (
    ChatDataAnomalyDetectionService,
)
from app.domain.services.chat_humanized_data_response_service import (
    ChatHumanizedDataResponseService,
)
from app.domain.services.chat_operational_data_commentary_service import (
    ChatOperationalDataCommentaryService,
)
from app.domain.services.chat_presentation_data_shape_analyzer import (
    ChatPresentationDataShapeAnalyzer,
)


class ChatDataInsightService:
    @classmethod
    def build(
        cls,
        metadata: dict[str, Any],
        data: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any] | None:
        if not isinstance(metadata, dict) or not isinstance(data, dict):
            return None

        if cls._is_scalar_kpi_response(metadata, data):
            commentary = cls._build_scalar_kpi_commentary(
                metadata,
                data,
                format_quantity=format_quantity,
            )
        else:
            profile_key = ChatOperationalDataCommentaryService.resolve_profile_key(
                path=str(metadata.get("path") or ""),
                metadata=metadata,
            )
            commentary = None

            if profile_key:
                commentary = ChatOperationalDataCommentaryService.build(
                    profile_key,
                    data,
                    format_quantity=format_quantity,
                )

            if not commentary:
                commentary = cls._build_generic_commentary(metadata, data)

        if not commentary:
            return None

        rows = cls._resolve_rows(metadata, data)
        anomalies = ChatDataAnomalyDetectionService.detect(rows=rows, metadata=metadata)
        anomaly_attention = ChatDataAnomalyDetectionService.attention_lines(anomalies)

        if anomalies:
            commentary["anomalies"] = anomalies

        if anomaly_attention:
            existing_attention = [
                str(line).strip()
                for line in (commentary.get("attention") or [])
                if str(line or "").strip()
            ]
            merged_attention = existing_attention[:]

            for line in anomaly_attention:
                if line not in merged_attention:
                    merged_attention.append(line)

            commentary["attention"] = merged_attention[:8]

        if rows is not None:
            shape = ChatPresentationDataShapeAnalyzer.analyze(rows=rows)
            visual_hints = cls._visual_hints_from_shape(shape)

            if visual_hints:
                commentary["visualHints"] = visual_hints

            if not commentary.get("derivedMetrics"):
                commentary["derivedMetrics"] = cls._build_derived_metrics(rows=rows, shape=shape)
        elif not commentary.get("visualHints"):
            commentary["visualHints"] = ["field_value_profile"]

        cls._apply_truncation_flags(commentary, metadata=metadata, data=data)

        data_answer = ChatHumanizedDataResponseService.to_data_answer(commentary)

        if not data_answer:
            return None

        return data_answer

    @classmethod
    def build_commentary_mirror(
        cls,
        data_answer: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        return ChatHumanizedDataResponseService.to_commentary_mirror(data_answer)

    @classmethod
    def _build_generic_commentary(
        cls,
        metadata: dict[str, Any],
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_humanized_data_response_content_service import (
            ChatHumanizedDataResponseContentService,
        )

        rows = cls._resolve_rows(metadata, data)

        if rows is None:
            return None

        shape = ChatPresentationDataShapeAnalyzer.analyze(rows=rows)
        highlights: list[str] = []
        attention: list[str] = []
        commentary: dict[str, Any] = {
            "profileKey": "generic_list",
        }

        if not rows:
            highlights.append(
                ChatHumanizedDataResponseContentService.get("generic", "emptyList")
            )
            commentary["highlights"] = highlights
            commentary["summaryLines"] = highlights
            return commentary

        highlights.append(
            ChatHumanizedDataResponseContentService.format(
                "generic",
                "rowCount",
                count=str(len(rows)),
            )
        )

        recommended = str(shape.get("recommended") or "table").strip()
        visual_label = ChatHumanizedDataResponseContentService.get(
            "visualHints",
            recommended,
            default=recommended,
        )

        if visual_label:
            highlights.append(
                ChatHumanizedDataResponseContentService.format(
                    "generic",
                    "shapeRecommend",
                    visual=visual_label,
                )
            )

        if int(shape.get("rows") or 0) > 25:
            attention.append(
                ChatHumanizedDataResponseContentService.get("generic", "largeList")
            )
            commentary["paginated"] = True

        numeric_keys = shape.get("numericKeys") or []

        if numeric_keys and rows:
            key = str(numeric_keys[0])
            values = [
                float(row.get(key))
                for row in rows
                if isinstance(row.get(key), (int, float)) and not isinstance(row.get(key), bool)
            ]

            if values:
                total = sum(values)
                highlights.append(
                    ChatHumanizedDataResponseContentService.format(
                        "generic",
                        "numericTotal",
                        field=key,
                        total=cls._format_number(total),
                    )
                )

        commentary["highlights"] = highlights
        commentary["attention"] = attention
        commentary["summaryLines"] = highlights[:4]
        commentary["derivedMetrics"] = cls._build_derived_metrics(rows=rows, shape=shape)

        return ChatHumanizedDataResponseService.normalize(
            commentary,
            profile_key="generic_list",
        )

    @classmethod
    def _apply_truncation_flags(
        cls,
        commentary: dict[str, Any],
        *,
        metadata: dict[str, Any],
        data: dict[str, Any],
    ) -> None:
        if commentary.get("paginated"):
            cls._ensure_truncation_limitations(commentary)
            return

        if cls._metadata_has_truncated_sections(metadata):
            commentary["paginated"] = True
        else:
            rows = cls._resolve_rows(metadata, data)

            if rows is not None and ChatDataAnomalyDetectionService._is_paginated(
                metadata, len(rows)
            ):
                commentary["paginated"] = True
            elif cls._composite_sections_truncated(metadata, data):
                commentary["paginated"] = True

        cls._ensure_truncation_limitations(commentary)

    @classmethod
    def _ensure_truncation_limitations(cls, commentary: dict[str, Any]) -> None:
        if not commentary.get("paginated"):
            return

        existing = [
            str(line).strip()
            for line in (commentary.get("limitations") or [])
            if str(line or "").strip()
        ]

        if existing:
            commentary["limitations"] = existing
            return

        commentary["limitations"] = ChatHumanizedDataResponseService._default_limitations(
            commentary
        )

    @classmethod
    def _metadata_has_truncated_sections(cls, metadata: dict[str, Any]) -> bool:
        api_meta = metadata.get("apiDelpiResponseMeta")

        if not isinstance(api_meta, dict):
            return False

        sections = api_meta.get("sections")

        if not isinstance(sections, list):
            return False

        return any(
            isinstance(section, dict) and section.get("truncated")
            for section in sections
        )

    @classmethod
    def _composite_sections_truncated(
        cls,
        metadata: dict[str, Any],
        data: dict[str, Any],
    ) -> bool:
        table_presentations: list[dict[str, Any]] = []

        tables = metadata.get("tablePresentations")

        if isinstance(tables, list):
            table_presentations.extend(
                table for table in tables if isinstance(table, dict)
            )

        single = metadata.get("tablePresentation")

        if isinstance(single, dict):
            table_presentations.append(single)

        import re

        for table in table_presentations:
            table_rows = table.get("rows")

            if not isinstance(table_rows, list) or not table_rows:
                continue

            shown = len(table_rows)
            table_id = str(table.get("tableId") or table.get("id") or "").strip().casefold()
            title = str(table.get("title") or "")
            role = str(table.get("role") or "").strip().casefold()
            title_match = re.search(r"(\d+)\s+de\s+(\d+)", title, re.IGNORECASE)

            if title_match:
                shown_in_title = int(title_match.group(1))
                total_in_title = int(title_match.group(2))

                if total_in_title > shown_in_title:
                    return True

            for section_key, hints in (
                ("production", ("production", "factoryproduction", "op")),
                ("shipping", ("shipping", "factoryshipping", "expedi")),
                ("raw_material_stock", ("stock", "rawmaterial", "mpstock", "matéria-prima", "materia-prima")),
            ):
                block = data.get(section_key)

                if not isinstance(block, dict):
                    continue

                title_token = title.casefold()
                matches_table = any(hint in table_id for hint in hints) or any(
                    hint in title_token for hint in hints
                )

                if section_key == "production" and role == "list":
                    matches_table = True

                if not matches_table:
                    continue

                items = block.get("items")

                if isinstance(items, list) and len(items) > shown:
                    return True

                summary = block.get("summary")

                if section_key == "production" and isinstance(summary, dict):
                    total_orders = int(summary.get("total_pa_orders") or 0) + int(
                        summary.get("total_pi_orders") or 0
                    )

                    if total_orders > shown:
                        return True

        return False

    @classmethod
    def _resolve_rows(
        cls,
        metadata: dict[str, Any],
        data: dict[str, Any],
    ) -> list[dict[str, Any]] | None:
        table = metadata.get("tablePresentation")

        if isinstance(table, dict):
            rows = table.get("rows")

            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]

        tables = metadata.get("tablePresentations")

        if isinstance(tables, list):
            for item in tables:
                if not isinstance(item, dict):
                    continue

                rows = item.get("rows")

                if isinstance(rows, list) and rows:
                    return [row for row in rows if isinstance(row, dict)]

        if isinstance(data.get("items"), list):
            return [row for row in data["items"] if isinstance(row, dict)]

        nested = data.get("data")

        if isinstance(nested, dict) and isinstance(nested.get("items"), list):
            return [row for row in nested["items"] if isinstance(row, dict)]

        if cls._is_scalar_kpi_response(metadata, data):
            return None

        if data and not isinstance(data.get("items"), list):
            nested_payload = data.get("data")

            if isinstance(nested_payload, dict) and cls._is_scalar_kpi_response(
                metadata,
                nested_payload,
            ):
                return None

            return []

        return None

    @classmethod
    def _api_response_meta(cls, metadata: dict[str, Any]) -> dict[str, Any]:
        api_meta = metadata.get("apiDelpiResponseMeta")

        return api_meta if isinstance(api_meta, dict) else {}

    @classmethod
    def _unwrap_scalar_payload(cls, data: dict[str, Any]) -> dict[str, Any]:
        nested = data.get("data")

        if isinstance(nested, dict):
            return nested

        return data

    @classmethod
    def _scalar_skip_keys(cls) -> frozenset[str]:
        return frozenset(
            {
                "branch",
                "branches",
                "start_date",
                "end_date",
                "date_start",
                "date_end",
                "end_date_exclusive",
                "month",
                "granularity",
                "enabled",
                "truncated",
                "sort_key",
                "indicator_id",
                "indicator_code",
                "indicator_name",
                "goal_mode",
                "goal_periodicity",
                "goal_scope_branch",
                "goal_scope_label",
                "goal_scope_hint",
                "scope_type",
                "performance_direction",
                "value_decimals",
                "value_prefix",
                "value_suffix",
                "value_unit",
                "has_goal",
                "comparable_goal",
                "goal_label",
                "goal_value",
                "period_reference",
                "periodo",
                "location",
                "unit",
            }
        )

    @classmethod
    def _scalar_metric_priority(cls) -> tuple[str, ...]:
        return (
            "rol",
            "value",
            "percentage",
            "current",
            "gross_revenue",
            "financial_balance",
            "target",
            "previous",
        )

    @classmethod
    def _is_scalar_kpi_response(
        cls,
        metadata: dict[str, Any],
        data: dict[str, Any],
    ) -> bool:
        if not isinstance(data, dict):
            return False

        api_meta = cls._api_response_meta(metadata)
        shape = str(api_meta.get("shape") or "").strip().lower()

        if shape == "scalar":
            return True

        if isinstance(data.get("items"), list):
            return False

        payload = cls._unwrap_scalar_payload(data)
        skip = cls._scalar_skip_keys()
        numeric_fields = [
            key
            for key, value in payload.items()
            if str(key) not in skip
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
        ]

        if not numeric_fields:
            return False

        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        entity = str(api_meta.get("entity") or "").strip() or None
        profile_key = ChatPresentationProfileService.resolve_profile_key(
            str(metadata.get("path") or ""),
            entity,
        )

        return profile_key in {
            "kpi_series",
            "generic_kpi_series",
            "kpi_snapshot",
            "kpi_dashboard",
        }

    @classmethod
    def _build_scalar_kpi_commentary(
        cls,
        metadata: dict[str, Any],
        data: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any] | None:
        from app.domain.services.external_actions.external_action_column_label_service import (
            ExternalActionColumnLabelService,
        )

        payload = cls._unwrap_scalar_payload(data)

        if not isinstance(payload, dict):
            return None

        api_meta = cls._api_response_meta(metadata)
        field_labels = api_meta.get("fields") if isinstance(api_meta.get("fields"), dict) else {}
        field_formats = (
            api_meta.get("fieldFormats") if isinstance(api_meta.get("fieldFormats"), dict) else {}
        )
        label_service = ExternalActionColumnLabelService()
        skip = cls._scalar_skip_keys()
        priority = cls._scalar_metric_priority()
        ordered_keys: list[str] = []

        for key in priority:
            if key in payload and key not in skip and isinstance(payload.get(key), (int, float)):
                ordered_keys.append(key)

        for key, value in payload.items():
            token = str(key)

            if token in skip or token in ordered_keys:
                continue

            if isinstance(value, (int, float)) and not isinstance(value, bool):
                ordered_keys.append(token)

        if not ordered_keys:
            return None

        def fmt(field_key: str, value: object) -> str:
            if format_quantity:
                return format_quantity(value, field_key)

            return label_service.format_field_value(
                field_key,
                value,
                schema_formats=field_formats,
            )

        highlights: list[str] = []

        for key in ordered_keys[:8]:
            label = str(field_labels.get(key) or key).strip()
            highlights.append(f"**{label}:** {fmt(key, payload.get(key))}")

        lead = highlights[0] if highlights else ""
        profile_key = "generic_kpi_series"

        return ChatHumanizedDataResponseService.normalize(
            {
                "profileKey": profile_key,
                "highlights": highlights,
                "attention": [],
                "summaryLines": highlights[:4],
                "alertLevel": "ok" if lead else "unknown",
                "summary": lead,
            },
            profile_key=profile_key,
        )

    @classmethod
    def _visual_hints_from_shape(cls, shape: dict[str, Any]) -> list[str]:
        recommended = str(shape.get("recommended") or "").strip()

        mapping = {
            "line_chart": "time_series",
            "horizontal_bar": "categorical_ranking",
            "donut": "composition",
            "tree": "hierarchy",
            "kpi": "kpi_set",
            "table": "generic_list",
            "text": "field_value_profile",
        }

        hint = mapping.get(recommended)

        return [hint] if hint else []

    @classmethod
    def _build_derived_metrics(
        cls,
        *,
        rows: list[dict[str, Any]] | None,
        shape: dict[str, Any],
    ) -> list[dict[str, str]]:
        from app.domain.services.chat_humanized_data_response_content_service import (
            ChatHumanizedDataResponseContentService,
        )

        safe_rows = [row for row in (rows or []) if isinstance(row, dict)]
        metrics: list[dict[str, str]] = [
            {
                "label": "Registros",
                "value": str(len(safe_rows)),
            }
        ]

        numeric_keys = shape.get("numericKeys") or []

        if numeric_keys and safe_rows:
            key = str(numeric_keys[0])
            values = [
                float(row.get(key))
                for row in safe_rows
                if isinstance(row.get(key), (int, float)) and not isinstance(row.get(key), bool)
            ]

            if values:
                total = sum(values)
                metrics.append(
                    {
                        "label": key,
                        "value": cls._format_number(total),
                    }
                )

                if len(values) > 1:
                    metrics.append(
                        {
                            "label": ChatHumanizedDataResponseContentService.get(
                                "derivedMetrics",
                                "averageLabel",
                                default="Média",
                            ),
                            "value": cls._format_number(total / len(values)),
                        }
                    )

        return metrics[:6]

    @classmethod
    def _format_number(cls, value: float) -> str:
        if abs(value - round(value)) < 0.0001:
            return str(int(round(value)))

        return f"{value:.2f}".rstrip("0").rstrip(".")
