"""Decisão genérica por forma dos dados — após intent operacional e preferência."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_chart_type_selection_service import (
    ChatChartTypeSelectionService,
)
from app.domain.services.chat_presentation_chart_decision_service import (
    ChatPresentationChartDecisionService,
)
from app.domain.services.chat_presentation_data_shape_analyzer import (
    ChatPresentationDataShapeAnalyzer,
)
from app.domain.services.chat_presentation_decision_builder_service import (
    ChatPresentationDecisionBuilderService,
)
from app.domain.services.chat_presentation_decision_metadata_service import (
    ChatPresentationDecisionMetadataService,
)
from app.domain.services.chat_presentation_operational_intent_decision_service import (
    ChatPresentationOperationalIntentDecisionService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)
from app.domain.services.chat_presentation_view_intent_service import (
    ChatPresentationViewIntentService,
)


class ChatPresentationGenericDecisionService:
    @classmethod
    def normalize_message(cls, user_message: str | None) -> str:
        return re.sub(r"\s+", " ", str(user_message or "").strip().lower())

    @classmethod
    def looks_like_checklist(cls, message: str) -> bool:
        if not message:
            return False

        return any(
            token in message
            for token in ChatPresentationVocabularyService.intent_markers("checklist")
        )

    @classmethod
    def looks_like_canvas(cls, message: str) -> bool:
        if not message:
            return False

        return any(
            token in message
            for token in ChatPresentationVocabularyService.intent_markers("canvas")
        )

    @classmethod
    def resolve_kpi_presentation(
        cls,
        *,
        primary_presentation: dict[str, Any] | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if isinstance(primary_presentation, dict) and primary_presentation.get("type") == "kpi":
            return primary_presentation

        if not isinstance(metadata, dict):
            return None

        kpi_slot = metadata.get("kpiPresentation")

        if isinstance(kpi_slot, dict) and kpi_slot.get("type") == "kpi":
            return kpi_slot

        return None

    @classmethod
    def resolve(
        cls,
        *,
        intent: str | None = None,
        rows: list[dict[str, Any]] | None = None,
        user_message: str | None = None,
        user_preference: str | None = None,
        primary_presentation: dict[str, Any] | None = None,
        table_presentation: dict[str, Any] | None = None,
        chart_presentation: dict[str, Any] | None = None,
        tree_presentation: dict[str, Any] | None = None,
        dashboard_presentation: dict[str, Any] | None = None,
        text_presentation: dict[str, Any] | None = None,
        available_formats: list[str] | None = None,
        path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        message = cls.normalize_message(user_message)
        reason = ChatPresentationVocabularyService.decision_reason
        build = ChatPresentationDecisionBuilderService.build
        merge = ChatPresentationDecisionBuilderService.merge_views

        if cls.looks_like_checklist(message):
            return build(
                selected="checklist",
                fallback="text",
                reason=reason("checklist"),
                available_views=["checklist", "text", "canvas"],
                rows=rows,
                intent=intent,
            )

        if cls.looks_like_canvas(message):
            return build(
                selected="canvas",
                fallback="text",
                reason=reason("canvas"),
                available_views=["canvas", "text"],
                rows=rows,
                intent=intent,
            )

        if ChatPresentationDecisionMetadataService.effective_tree_presentation(
            tree_presentation=tree_presentation,
            primary_presentation=primary_presentation,
        ) and not ChatPresentationOperationalIntentDecisionService.should_default_analyser_stack_to_text(
            path=path,
            text_presentation=text_presentation,
            user_preference=user_preference,
        ):
            return build(
                selected="tree",
                fallback="table",
                reason=reason("treeHierarchy"),
                available_views=merge(available_formats, ["tree", "table", "text"]),
                rows=rows,
                intent=intent,
            )

        if dashboard_presentation or (
            primary_presentation and primary_presentation.get("type") == "dashboard"
        ):
            return build(
                selected="dashboard",
                fallback="table",
                reason=reason("dashboard"),
                available_views=merge(
                    available_formats,
                    ["dashboard", "table", "chart", "kpi"],
                ),
                rows=rows,
                intent=intent,
            )

        kpi_presentation = cls.resolve_kpi_presentation(
            primary_presentation=primary_presentation,
            metadata=metadata,
        )

        if kpi_presentation:
            return build(
                selected="kpi",
                fallback="table",
                reason=reason("kpiSingle"),
                available_views=merge(
                    available_formats,
                    ["kpi", "table", "chart", "text", "dashboard"],
                ),
                rows=rows,
                intent=intent,
            )

        table_rows = rows or ChatPresentationDecisionMetadataService.rows_from_metadata_tables(
            metadata if isinstance(metadata, dict) else None,
        ) or ChatPresentationDecisionMetadataService.rows_from_presentation(
            table_presentation
            or (
                primary_presentation
                if primary_presentation and primary_presentation.get("type") == "table"
                else None
            )
        )

        shape = ChatPresentationDataShapeAnalyzer.analyze(rows=table_rows)

        if shape["rows"] == 0:
            return build(
                selected="text",
                fallback="text",
                reason=reason("noTabularData"),
                available_views=["text"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        entity = ChatPresentationDecisionMetadataService.resolve_entity(
            metadata if isinstance(metadata, dict) else None,
            path=path,
        )

        prefer_table = ChatPresentationViewIntentService.prefers_table_for_automatic(
            path=path,
            entity=entity,
            data_shape=shape,
            user_message=message,
            has_table=bool(table_rows),
        )

        if prefer_table:
            return build(
                selected="table",
                fallback="text",
                reason=reason("auditableList"),
                available_views=merge(available_formats, ["table", "chart", "text", "kpi"]),
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if (chart_presentation or (
            primary_presentation and primary_presentation.get("type") == "chart"
        )) and not prefer_table:
            chart_type = ChatPresentationChartDecisionService.resolve_chart_type(
                table_rows=table_rows,
                shape=shape,
                user_message=message,
                fallback_chart=str(
                    (chart_presentation or primary_presentation or {}).get("chartType") or "bar"
                ),
            )
            selected = ChatPresentationChartDecisionService.chart_type_to_selected(chart_type)

            return build(
                selected=selected,
                fallback="table",
                reason=ChatPresentationChartDecisionService.chart_reason(chart_type, shape),
                available_views=merge(available_formats, [selected, "table", "chart", "text"]),
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if shape["rows"] == 1 and shape["hasNumeric"] and len(shape.get("numericKeys") or []) == 1:
            if prefer_table:
                return build(
                    selected="table",
                    fallback="text",
                    reason=reason("auditableList"),
                    available_views=merge(available_formats, ["table", "chart", "text", "kpi"]),
                    rows=table_rows,
                    intent=intent,
                    data_shape=shape,
                )

            return build(
                selected="kpi",
                fallback="table",
                reason=reason("singleNumericKpi"),
                available_views=["kpi", "table", "chart"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if shape["hasHierarchy"]:
            return build(
                selected="tree",
                fallback="table",
                reason=reason("hierarchyDetected"),
                available_views=["tree", "table"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        numeric_keys = list(shape.get("numericKeys") or [])

        if len(numeric_keys) >= 2 and table_rows:
            lowered = {key.lower() for key in numeric_keys}
            has_target = any(
                any(token in key for token in ("meta", "target", "goal", "objetivo"))
                for key in lowered
            )
            has_actual = any(
                any(token in key for token in ("realizado", "actual", "atual", "valor"))
                for key in lowered
            )

            if has_target and has_actual or any(
                token in message for token in ("versus", " vs ", "meta", "compar")
            ):
                label_key = shape.get("labelKey") or "label"
                chart_type = ChatChartTypeSelectionService.resolve(
                    rows=table_rows[:24],
                    label_key=str(label_key),
                    numeric_keys=numeric_keys[:3],
                    user_message=message or None,
                )
                selected = ChatPresentationChartDecisionService.chart_type_to_selected(chart_type)

                return build(
                    selected=selected,
                    fallback="table",
                    reason=reason("targetVsActual"),
                    available_views=merge(
                        available_formats,
                        [selected, "kpi", "table", "chart"],
                    ),
                    rows=table_rows,
                    intent=intent,
                    data_shape=shape,
                )

        if shape["hasDate"] and shape["hasNumeric"] and table_rows:
            label_key = shape.get("labelKey") or "label"
            chart_type = ChatChartTypeSelectionService.resolve(
                rows=table_rows[:24],
                label_key=str(label_key),
                numeric_keys=numeric_keys or ["value"],
                user_message=message or None,
            )
            selected = ChatPresentationChartDecisionService.chart_type_to_selected(chart_type)

            return build(
                selected=selected,
                fallback="table",
                reason=reason("temporalNumeric"),
                available_views=merge(available_formats, [selected, "table", "chart"]),
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if shape["hasNumeric"] and shape["categoryCardinality"] > 6 and table_rows:
            return build(
                selected="horizontal_bar",
                fallback="table",
                reason=reason("manyCategoriesRanking"),
                available_views=["horizontal_bar", "table", "chart"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if shape["hasNumeric"] and 3 <= shape["categoryCardinality"] <= 6 and table_rows:
            label_key = shape.get("labelKey") or "label"
            chart_type = ChatChartTypeSelectionService.resolve(
                rows=table_rows[:12],
                label_key=str(label_key),
                numeric_keys=list(shape.get("numericKeys") or ["value"]),
                user_message=message or None,
            )
            selected = ChatPresentationChartDecisionService.chart_type_to_selected(chart_type)

            return build(
                selected=selected,
                fallback="table",
                reason=reason("categoryParticipation"),
                available_views=[selected, "table", "chart"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if text_presentation and not table_rows:
            return build(
                selected="text",
                fallback="text",
                reason=reason("explanatoryNoTable"),
                available_views=["text"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        return build(
            selected="table",
            fallback="text",
            reason=reason("auditableList"),
            available_views=merge(available_formats, ["table", "chart", "text"]),
            rows=table_rows,
            intent=intent,
            data_shape=shape,
        )
