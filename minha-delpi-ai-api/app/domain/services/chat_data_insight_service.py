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

        shape = ChatPresentationDataShapeAnalyzer.analyze(rows=rows)
        visual_hints = cls._visual_hints_from_shape(shape)

        if visual_hints:
            commentary["visualHints"] = visual_hints

        if not commentary.get("derivedMetrics"):
            commentary["derivedMetrics"] = cls._build_derived_metrics(rows=rows, shape=shape)

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

        if data and not isinstance(data.get("items"), list):
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
