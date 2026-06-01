"""Agrega linhas de gráfico repetidas no mesmo eixo de categoria (ex.: filial)."""

from __future__ import annotations

from typing import Any

_PERCENT_HINTS = (
    "percent",
    "pct",
    "eficiencia",
    "efficiency",
    "taxa",
    "yield",
    "rate",
)
_SUM_HINTS = (
    "count",
    "qtd",
    "quantidade",
    "qty",
    "hours",
    "horas",
    "mod",
    "resultado",
    "lucro",
    "prejuizo",
    "apont",
    "profit",
    "loss",
)
_WEIGHT_KEYS = (
    "tempo_real_horas",
    "real_hours",
    "planned_hours",
    "tempo_previsto_horas",
)


class ChatChartDataAggregationService:
    @classmethod
    def should_aggregate(
        cls,
        rows: list[dict[str, Any]],
        category_key: str,
    ) -> bool:
        if not category_key or len(rows) < 2:
            return False

        labels = [str(row.get(category_key, "")).strip() for row in rows if isinstance(row, dict)]

        if len(labels) < 2:
            return False

        return len(set(labels)) < len(labels)

    @classmethod
    def aggregate_by_category(
        cls,
        rows: list[dict[str, Any]],
        category_key: str,
        value_keys: list[str],
    ) -> list[dict[str, Any]]:
        if not cls.should_aggregate(rows, category_key):
            return rows

        grouped: dict[str, list[dict[str, Any]]] = {}

        for row in rows:
            if not isinstance(row, dict):
                continue

            label = str(row.get(category_key, "")).strip()

            if label not in grouped:
                grouped[label] = []

            grouped[label].append(row)

        aggregated: list[dict[str, Any]] = []

        for label in sorted(grouped.keys(), key=cls._category_sort_key):
            chunk = grouped[label]
            item: dict[str, Any] = {category_key: label}

            for key in value_keys:
                if key == category_key:
                    continue

                item[key] = cls._aggregate_metric(chunk, key)

            aggregated.append(item)

        return aggregated

    @classmethod
    def apply_to_chart_presentation(cls, presentation: dict[str, Any]) -> None:
        if presentation.get("type") != "chart":
            return

        chart_type = str(presentation.get("chartType") or "bar").strip().lower()

        if chart_type in {"scatter", "heatmap", "gauge"}:
            return

        config = presentation.get("config")

        if not isinstance(config, dict):
            return

        category_key = str(config.get("xAxis") or "").strip()
        y_axis = config.get("yAxis")
        value_keys = (
            [str(key) for key in y_axis if key]
            if isinstance(y_axis, list)
            else [str(y_axis)]
            if isinstance(y_axis, str) and y_axis
            else []
        )

        if not category_key or not value_keys:
            return

        data = presentation.get("data")

        if not isinstance(data, list) or not data:
            return

        presentation["data"] = cls.aggregate_by_category(
            [row for row in data if isinstance(row, dict)],
            category_key,
            value_keys,
        )

    @classmethod
    def _aggregate_metric(cls, rows: list[dict[str, Any]], key: str) -> float:
        values = [
            float(row[key])
            for row in rows
            if isinstance(row.get(key), (int, float))
        ]

        if not values:
            return 0.0

        lowered = str(key or "").lower()

        if any(token in lowered for token in _PERCENT_HINTS):
            weight_key = next((candidate for candidate in _WEIGHT_KEYS if candidate in rows[0]), None)

            if weight_key:
                total_weight = sum(
                    float(row.get(weight_key) or 0)
                    for row in rows
                    if isinstance(row.get(weight_key), (int, float))
                )

                if total_weight > 0:
                    weighted = sum(
                        float(row.get(key) or 0) * float(row.get(weight_key) or 0)
                        for row in rows
                        if isinstance(row.get(key), (int, float))
                        and isinstance(row.get(weight_key), (int, float))
                    )

                    return round(weighted / total_weight, 4)

            return round(sum(values) / len(values), 4)

        if any(token in lowered for token in _SUM_HINTS):
            return round(sum(values), 4)

        return round(sum(values) / len(values), 4)

    @staticmethod
    def _category_sort_key(label: str) -> tuple:
        stripped = str(label).strip()

        if stripped.isdigit():
            return (0, int(stripped), stripped)

        return (1, stripped.lower(), stripped)
