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
from app.domain.services.chat_operational_user_question_synthesis_service import (
    ChatOperationalUserQuestionSynthesisService,
)
from app.domain.services.chat_presentation_data_shape_analyzer import (
    ChatPresentationDataShapeAnalyzer,
)

from app.domain.services.chat_presentation_scalar_field_commentary_service import (
    ChatPresentationScalarFieldCommentaryService,
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

        if ChatPresentationScalarFieldCommentaryService.matches(metadata, data):
            commentary = ChatPresentationScalarFieldCommentaryService.build(
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

        profile_key = str(
            commentary.get("profileKey")
            or ChatOperationalDataCommentaryService.resolve_profile_key(
                path=str(metadata.get("path") or ""),
                metadata=metadata,
            )
            or ""
        ).strip()
        user_message = str(metadata.get("userMessage") or "").strip() or None

        if user_message:
            commentary = ChatOperationalUserQuestionSynthesisService.apply(
                commentary,
                data=data,
                metadata=metadata,
                user_message=user_message,
                profile_key=profile_key or None,
            )

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
            from app.domain.services.chat_humanized_data_response_content_service import (
                ChatHumanizedDataResponseContentService,
            )

            hint = ChatHumanizedDataResponseContentService.get(
                "scalarFieldProfile",
                "visualHint",
                default="field_value_profile",
            )
            commentary["visualHints"] = [hint]

        cls._apply_truncation_flags(commentary, metadata=metadata, data=data)

        from app.domain.services.chat_operational_result_completeness_service import (
            ChatOperationalResultCompletenessService,
        )

        ChatOperationalResultCompletenessService.apply_to_commentary(
            commentary,
            metadata=metadata,
            data=data,
        )

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
            from app.domain.services.chat_operational_result_completeness_service import (
                ChatOperationalResultCompletenessService,
            )

            response_meta = metadata.get("apiDelpiResponseMeta")
            response_meta = response_meta if isinstance(response_meta, dict) else None
            incomplete = ChatOperationalResultCompletenessService.is_incomplete(
                data,
                response_meta=response_meta,
            )

            if not incomplete and not commentary.get("paginated"):
                attention.append(
                    ChatHumanizedDataResponseContentService.get("generic", "largeList")
                )

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

        raw_materials = data.get("raw_materials")

        if isinstance(raw_materials, list) and raw_materials:
            return [row for row in raw_materials if isinstance(row, dict)]

        nested = data.get("data")

        if isinstance(nested, dict) and isinstance(nested.get("items"), list):
            return [row for row in nested["items"] if isinstance(row, dict)]

        if ChatPresentationScalarFieldCommentaryService.matches(metadata, data):
            return None

        if data and not isinstance(data.get("items"), list):
            nested_payload = data.get("data")

            if isinstance(nested_payload, dict) and ChatPresentationScalarFieldCommentaryService.matches(
                metadata,
                nested_payload,
            ):
                return None

            return []

        return None

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
