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



class ExternalActionKpiChartSpecializedService:
    @staticmethod
    def _build_analyser_structure_type_chart(presenter: ExternalActionKpiChartPresenter, root: dict) -> dict | None:
        structure = root.get("structure")

        if not isinstance(structure, dict):
            return None

        counts: dict[str, int] = {}

        for item in structure.get("items") or []:
            if not isinstance(item, dict):
                continue

            components = [
                component
                for component in (item.get("components") or [])
                if isinstance(component, dict)
            ]

            if components:
                for component in components:
                    fallback = presenter._host._presenter_text("charts", "componentTypeFallback")
                    comp_type = (
                        str(component.get("type") or fallback).strip().upper()
                        or fallback.upper()
                    )
                    counts[comp_type] = counts.get(comp_type, 0) + 1

                continue

            fallback = presenter._host._presenter_text("charts", "componentTypeFallback")
            comp_type = (
                str(item.get("type") or fallback).strip().upper() or fallback.upper()
            )
            counts[comp_type] = counts.get(comp_type, 0) + 1

        if len(counts) < 2:
            return None

        sorted_counts = sorted(counts.items(), key=lambda pair: -pair[1])
        labels = [
            presenter._host._presenter_text(
                "charts",
                "typeLabelWithCount",
                type=key,
                count=str(value),
            )
            for key, value in sorted_counts
        ]
        values = [value for _, value in sorted_counts]
        label_key = "label"
        value_key = "value"
        chart_rows = [
            {label_key: label, value_key: value}
            for label, value in zip(labels, values)
        ]

        return {
            "type": "chart",
            "chartType": "donut",
            "title": presenter._host._presenter_text("charts", "structureTypeCompositionTitle"),
            "data": chart_rows,
            "config": {
                "xAxis": label_key,
                "yAxis": value_key,
                "legend": False,
            },
        }

    @staticmethod
    def _is_stock_data(presenter: ExternalActionKpiChartPresenter, row: dict) -> bool:
        return "warehouse" in row and (
            "available_quantity" in row or "current_quantity" in row
        )

    @staticmethod
    def _collect_stock_items(presenter: ExternalActionKpiChartPresenter, root: dict) -> list | None:
        if not isinstance(root, dict):
            return None

        items = root.get("items")

        if (
            isinstance(items, list)
            and items
            and isinstance(items[0], dict)
            and presenter._is_stock_data(items[0])
        ):
            return items

        stock = root.get("stock")

        if isinstance(stock, dict):
            stock_items = stock.get("items")

            if (
                isinstance(stock_items, list)
                and stock_items
                and isinstance(stock_items[0], dict)
                and presenter._is_stock_data(stock_items[0])
            ):
                return stock_items

        return None

    @staticmethod
    def _build_stock_chart(presenter: ExternalActionKpiChartPresenter, items: list) -> dict | None:
        if not items:
            return None

        chart_data = []

        for item in items[:20]:
            if not isinstance(item, dict):
                continue

            label = presenter._host._presenter_text(
                "charts",
                "stockLocationLabel",
                branch=str(item.get("branch") or "?"),
                warehouse=str(item.get("warehouse") or "?"),
            )
            chart_data.append(
                {
                    "name": label,
                    presenter._host._humanize_key("current_quantity"): item.get("current_quantity") or 0,
                    presenter._host._humanize_key("available_quantity"): item.get("available_quantity") or 0,
                    presenter._host._humanize_key("committed_quantity"): item.get("committed_quantity") or 0,
                }
            )

        if not chart_data:
            return None

        quantity_series = [
            presenter._host._humanize_key("current_quantity"),
            presenter._host._humanize_key("available_quantity"),
            presenter._host._humanize_key("committed_quantity"),
        ]

        return {
            "type": "chart",
            "title": presenter._host._presenter_text("charts", "stockByLocationTitle"),
            "chartType": "horizontal_bar",
            "data": chart_data,
            "config": {
                "xAxis": "name",
                "yAxis": quantity_series,
                "colors": ["#0ea5e9", "#10b981", "#f59e0b"],
                "legend": True,
            },
        }

