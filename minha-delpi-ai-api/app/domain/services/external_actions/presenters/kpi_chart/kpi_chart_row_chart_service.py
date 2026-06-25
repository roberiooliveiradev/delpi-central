"""Delegate — KPI/chart presenter."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.external_actions.presenters.kpi_chart.kpi_chart_constants import (
    CHART_WORTHY_NUMERIC_KEYS,
    NO_CHART_PATHS,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.presenters.kpi_chart_presenter import (
        ExternalActionKpiChartPresenter,
    )



class ExternalActionKpiChartRowChartService:
    @staticmethod
    def _build_categorical_count_chart(
        presenter: ExternalActionKpiChartPresenter,
        rows: list,
        *,
        path: str = "",
    ) -> dict | None:
        if not rows or not isinstance(rows[0], dict):
            return None

        preferred_keys = (
            "status",
            "listing_kind",
            "filial",
            "branch",
            "sale_number",
            "op",
            "produto",
            "product_code",
        )
        first = rows[0]
        label_key = next(
            (key for key in preferred_keys if key in first and isinstance(first.get(key), str)),
            None,
        )

        if not label_key:
            label_key = next(
                (key for key, value in first.items() if isinstance(value, str) and str(value).strip()),
                None,
            )

        if not label_key:
            return None

        counts: dict[str, int] = {}

        for row in rows[:24]:
            if not isinstance(row, dict):
                continue

            label = str(row.get(label_key) or "").strip() or "—"
            counts[label] = counts.get(label, 0) + 1

        if not counts:
            return None

        data = [{"name": name, "value": value} for name, value in counts.items()]
        chart_title = presenter._host._infer_items_title(rows, path) or presenter._host._presenter_text(
            "charts",
            "defaultVisualizationTitle",
        )

        return {
            "type": "chart",
            "title": chart_title,
            "chartType": "donut",
            "data": data,
            "config": {
                "xAxis": "name",
                "yAxis": ["value"],
                "legend": len(data) > 1,
            },
        }

    @staticmethod
    def try_chart_from_rows(
        presenter: ExternalActionKpiChartPresenter,
        rows: list,
        *,
        force: bool = False,
        path: str = "",
        user_message: str | None = None,
    ) -> dict | None:
        """Gera gráfico APENAS quando os dados são naturalmente visuais (ou force=True)."""
        if len(rows) < 2 or not isinstance(rows[0], dict):
            return None

        heatmap = presenter.try_heatmap_from_rows(
            rows,
            force=force,
            user_message=user_message,
        )

        if heatmap:
            return heatmap

        if not force and len(rows) > 12:
            return None

        first = rows[0]
        numeric_keys = [key for key, value in first.items() if isinstance(value, (int, float))]
        string_keys = [key for key, value in first.items() if isinstance(value, str)]

        if not numeric_keys or not string_keys:
            return None

        if force:
            chart_numeric = numeric_keys[:3]
        else:
            chart_numeric = [
                key
                for key in numeric_keys
                if any(token in key.lower() for token in CHART_WORTHY_NUMERIC_KEYS)
            ]

            if not chart_numeric:
                return None

        from app.domain.services.chat_operational_group_by_refinement_service import (
            ChatOperationalGroupByRefinementService,
        )

        label_key = next(
            (
                key
                for key in (*ChatOperationalGroupByRefinementService.chart_axis_fields(), *string_keys)
                if key in string_keys
            ),
            string_keys[0],
        )
        labels = [str(row.get(label_key, "")) for row in rows[:12]]

        if len(set(labels)) < 2:
            return None

        from app.domain.services.chat_chart_type_selection_service import (
            ChatChartTypeSelectionService,
        )

        chart_numeric_slice = chart_numeric[:3]
        chart_type = ChatChartTypeSelectionService.resolve(
            rows=rows[:12],
            label_key=label_key,
            numeric_keys=chart_numeric_slice,
            user_message=user_message,
        )

        lowered_path = str(path or "").lower()

        if chart_type == "scatter" and (
            "eficiencia-fabril" in lowered_path or "eficiencia_fabril" in lowered_path
        ):
            if "filial" in string_keys:
                chart_type = "bar"
                label_key = "filial"

        config: dict = {
            "xAxis": label_key,
            "yAxis": chart_numeric_slice,
            "legend": len(chart_numeric_slice) > 1,
        }

        from app.domain.services.chat_presentation_axis_preference_service import (
            ChatPresentationAxisPreferenceService,
        )

        axis = ChatPresentationAxisPreferenceService.resolve(
            rows=rows[:12],
            chart_type=chart_type,
            label_key=label_key,
            numeric_keys=chart_numeric_slice,
            user_message=user_message,
        )

        config["xAxis"] = axis["xAxis"]
        config["yAxis"] = axis["yAxis"]
        config["numericColumns"] = axis["numericColumns"]
        config["categoryColumns"] = axis["categoryColumns"]

        if chart_type == "scatter":
            config["legend"] = False

        if chart_type == "combo" and len(chart_numeric_slice) >= 2:
            config["comboBarKey"] = chart_numeric_slice[0]
            config["comboLineKey"] = chart_numeric_slice[1]

        if chart_type == "gauge" and chart_numeric_slice:
            config["gaugeValueKey"] = chart_numeric_slice[0]
            config["gaugeTargetKey"] = (
                chart_numeric_slice[1] if len(chart_numeric_slice) > 1 else None
            )

        chart_title = presenter._host._infer_items_title(rows, path) or presenter._host._presenter_text(
            "charts",
            "defaultVisualizationTitle",
        )

        presentation = {
            "type": "chart",
            "title": chart_title,
            "chartType": chart_type,
            "data": rows,
            "config": config,
        }

        from app.domain.services.chat_chart_data_aggregation_service import (
            ChatChartDataAggregationService,
        )

        ChatChartDataAggregationService.apply_to_chart_presentation(presentation)

        capped = presentation.get("data") or []

        if isinstance(capped, list):
            presentation["data"] = capped[:24]

        return presentation

    @staticmethod
    def try_heatmap_from_rows(
        presenter: ExternalActionKpiChartPresenter,
        rows: list,
        *,
        force: bool = False,
        user_message: str | None = None,
    ) -> dict | None:
        if len(rows) < 4 or not isinstance(rows[0], dict):
            return None

        first = rows[0]
        string_keys = [key for key, value in first.items() if isinstance(value, str)]
        numeric_keys = [key for key, value in first.items() if isinstance(value, (int, float))]

        if len(string_keys) < 2 or len(numeric_keys) != 1:
            return None

        from app.domain.services.chat_chart_type_selection_service import (
            ChatChartTypeSelectionService,
        )

        message = re.sub(r"\s+", " ", str(user_message or "").strip().lower())
        wants_heatmap = any(
            token in message
            for token in ("heatmap", "mapa de calor", "mapa calor", "matriz de intensidade")
        )

        if not force and not wants_heatmap:
            if "item_code" in first and "description" in first:
                return None

            if not ChatChartTypeSelectionService._looks_heatmap_matrix(
                rows,
                string_keys,
                numeric_keys,
            ):
                return None

        x_axis, y_axis = ChatChartTypeSelectionService._pick_heatmap_axes(string_keys, rows)
        value_key = numeric_keys[0]
        capped_rows = rows[:144]

        return {
            "type": "chart",
            "title": presenter._host._presenter_text("charts", "heatmapTitle"),
            "chartType": "heatmap",
            "data": capped_rows,
            "config": {
                "xAxis": x_axis,
                "yAxis": y_axis,
                "valueKey": value_key,
                "legend": False,
            },
        }

