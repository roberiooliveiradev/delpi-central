"""Decisão e política de gráficos — tipo, reason e cap de dados."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_chart_type_selection_service import (
    ChatChartTypeSelectionService,
)
from app.domain.services.chat_presentation_chart_policy_service import (
    ChatPresentationChartPolicyService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)

_SELECTED_TO_CHART_TYPE = {
    "line_chart": "line",
    "area_chart": "area",
    "bar_chart": "bar",
    "horizontal_bar": "horizontal_bar",
    "donut": "donut",
    "grouped_bar": "grouped_bar",
    "stacked_bar": "stacked_bar",
    "combo_chart": "combo",
    "histogram": "histogram",
    "heatmap": "heatmap",
    "gauge": "gauge",
    "scatter": "scatter",
    "chart": "bar",
}

_CHART_TYPE_TO_SELECTED = {
    "line": "line_chart",
    "multi_line": "line_chart",
    "area": "area_chart",
    "bar": "bar_chart",
    "horizontal_bar": "horizontal_bar",
    "donut": "donut",
    "pie": "donut",
    "grouped_bar": "grouped_bar",
    "stacked_bar": "stacked_bar",
    "combo": "combo_chart",
    "histogram": "histogram",
    "heatmap": "heatmap",
    "gauge": "gauge",
    "scatter": "scatter",
}


class ChatPresentationChartDecisionService:
    @classmethod
    def chart_type_to_selected(cls, chart_type: str) -> str:
        return _CHART_TYPE_TO_SELECTED.get(chart_type, "chart")

    @classmethod
    def selected_to_chart_type(cls, selected: str) -> str | None:
        return _SELECTED_TO_CHART_TYPE.get(selected)

    @classmethod
    def resolve_chart_type(
        cls,
        *,
        table_rows: list[dict[str, Any]],
        shape: dict[str, Any],
        user_message: str,
        fallback_chart: str,
    ) -> str:
        if table_rows and shape.get("hasNumeric"):
            label_key = str(shape.get("labelKey") or "label")
            numeric_keys = list(shape.get("numericKeys") or ["value"])

            return ChatChartTypeSelectionService.resolve(
                rows=table_rows[:24],
                label_key=label_key,
                numeric_keys=numeric_keys,
                user_message=user_message or None,
            )

        return str(fallback_chart or "bar").strip() or "bar"

    @classmethod
    def chart_reason(cls, chart_type: str, shape: dict[str, Any]) -> str:
        reason = ChatPresentationVocabularyService.decision_reason

        if chart_type in {"line", "multi_line", "area"}:
            return reason("temporalNumeric")

        if chart_type in {"donut", "pie"}:
            return reason("categoryParticipation")

        if chart_type == "horizontal_bar":
            return reason("chartRankingLongNames")

        if shape.get("rows", 0) > 6:
            return reason("chartCategoryVolume")

        return reason("chartComparableNumeric")

    @classmethod
    def apply_category_aggregation(cls, metadata: dict[str, Any]) -> None:
        from app.domain.services.chat_chart_data_aggregation_service import (
            ChatChartDataAggregationService,
        )

        for key in ("chartPresentation", "presentation"):
            presentation = metadata.get(key)

            if not isinstance(presentation, dict) or presentation.get("type") != "chart":
                continue

            ChatChartDataAggregationService.apply_to_chart_presentation(presentation)

        dashboard = metadata.get("presentation")

        if not isinstance(dashboard, dict) or dashboard.get("type") != "dashboard":
            return

        for panel in dashboard.get("panels") or []:
            if not isinstance(panel, dict):
                continue

            chart = panel.get("chartPresentation")

            if isinstance(chart, dict) and chart.get("type") == "chart":
                ChatChartDataAggregationService.apply_to_chart_presentation(chart)

            presentation = panel.get("presentation")

            if isinstance(presentation, dict) and presentation.get("type") == "chart":
                ChatChartDataAggregationService.apply_to_chart_presentation(presentation)

    @classmethod
    def apply_policy_to_metadata(
        cls,
        metadata: dict[str, Any],
        decision: dict[str, Any],
        *,
        user_message: str | None = None,
    ) -> str | None:
        selected = str(decision.get("selected") or "")
        chart_type = cls.selected_to_chart_type(selected)

        if not chart_type:
            return None

        notices: list[str] = []

        for key in ("presentation", "chartPresentation"):
            presentation = metadata.get(key)

            if not isinstance(presentation, dict) or presentation.get("type") != "chart":
                continue

            config = presentation.get("config")

            if not isinstance(config, dict):
                config = {}
                presentation["config"] = config

            label_key = str(config.get("xAxis") or decision.get("dataShape", {}).get("labelKey") or "")
            y_axis = config.get("yAxis")
            value_key = y_axis[0] if isinstance(y_axis, list) and y_axis else None

            original = presentation.get("data") or []
            original_count = len(original) if isinstance(original, list) else 0

            capped = ChatPresentationChartPolicyService.apply(
                original if isinstance(original, list) else [],
                chart_type,
                label_key=label_key or None,
                value_key=str(value_key) if value_key else None,
            )

            presentation["chartType"] = chart_type
            config["recommendedChartType"] = chart_type
            presentation["data"] = capped

            from app.domain.services.chat_presentation_axis_preference_service import (
                ChatPresentationAxisPreferenceService,
            )

            ChatPresentationAxisPreferenceService.apply_to_chart_config(
                presentation,
                user_message=user_message,
            )

            from app.domain.services.chat_chart_data_aggregation_service import (
                ChatChartDataAggregationService,
            )

            ChatChartDataAggregationService.apply_to_chart_presentation(presentation)

            notice = ChatPresentationChartPolicyService.fallback_notice(
                chart_type,
                original_count,
                len(capped),
            )

            if notice:
                notices.append(notice)

        return notices[0] if notices else None
