"""Agregação tabular genérica — reutilizada por gráficos e refinamento de sessão."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_chart_data_aggregation_service import (
    ChatChartDataAggregationService,
)


class ChatTabularDataAggregationService:
    @classmethod
    def extract_items(cls, root: object) -> list[dict[str, Any]]:
        if not isinstance(root, dict):
            return []

        items = root.get("items")

        if isinstance(items, list):
            return [row for row in items if isinstance(row, dict)]

        rows = root.get("rows")

        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]

        data = root.get("data")

        if isinstance(data, dict):
            return cls.extract_items(data)

        return []

    @classmethod
    def can_aggregate(
        cls,
        rows: list[dict[str, Any]],
        *,
        category_field: str,
        metric_fields: list[str],
    ) -> bool:
        category = str(category_field or "").strip()

        if not category or not metric_fields:
            return False

        if len(rows) < 1:
            return False

        populated = 0

        for row in rows:
            if not isinstance(row, dict):
                continue

            label = str(row.get(category) or "").strip()

            if not label:
                continue

            if any(isinstance(row.get(key), (int, float)) for key in metric_fields):
                populated += 1

        return populated >= 1

    @classmethod
    def aggregate_ranking(
        cls,
        rows: list[dict[str, Any]],
        *,
        category_field: str,
        metric_fields: list[str],
        sort_field: str | None = None,
        descending: bool = True,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        category = str(category_field or "").strip()
        metrics = [str(key).strip() for key in metric_fields if str(key).strip()]

        if not category or not metrics:
            return rows

        aggregated = ChatChartDataAggregationService.aggregate_by_category(
            rows,
            category,
            metrics,
        )

        sort_key = str(sort_field or metrics[0] or "").strip()

        if sort_key:

            def sort_value(row: dict[str, Any]) -> float:
                value = row.get(sort_key)

                if isinstance(value, (int, float)):
                    return float(value)

                return 0.0

            aggregated.sort(key=sort_value, reverse=descending)

        if limit is not None and limit >= 1:
            aggregated = aggregated[: int(limit)]

        return aggregated
