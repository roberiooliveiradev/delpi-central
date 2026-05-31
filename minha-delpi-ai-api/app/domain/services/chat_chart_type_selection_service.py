"""Seleção automática de chartType — Playbook ampliação de gráficos, Fases 2–3."""

from __future__ import annotations

import re
from typing import Any


_TEMPORAL_LABEL_TOKENS = (
    "period",
    "periodo",
    "período",
    "month",
    "mes",
    "mês",
    "year",
    "ano",
    "date",
    "data",
    "week",
    "semana",
    "day",
    "dia",
)

_PARTICIPATION_HINTS = (
    "particip",
    "percent",
    "perc",
    "share",
    "fatia",
    "pizza",
    "rosca",
    "donut",
    "composição",
    "composicao",
)

_HORIZONTAL_HINTS = (
    "horizontal",
    "ranking",
    "top ",
    "top10",
    "top 10",
    "mais vendidos",
    "maiores",
)

_STACKED_HINTS = (
    "empilh",
    "stacked",
    "acumulad",
)

_COMBO_VALUE_KEYS = ("realizado", "actual", "atual", "value", "current", "valor")
_COMBO_TARGET_KEYS = ("meta", "target", "goal", "objetivo")


class ChatChartTypeSelectionService:
    @classmethod
    def resolve(
        cls,
        *,
        rows: list[dict[str, Any]],
        label_key: str,
        numeric_keys: list[str],
        user_message: str | None = None,
    ) -> str:
        message = re.sub(r"\s+", " ", str(user_message or "").strip().lower())

        if message:
            hinted = cls._resolve_from_message(message)

            if hinted:
                return hinted

        string_keys = [
            key
            for key, value in (rows[0] or {}).items()
            if isinstance(value, str)
        ]

        if cls._looks_heatmap_matrix(rows, string_keys, numeric_keys):
            return "heatmap"

        if cls._looks_gauge(rows, numeric_keys):
            return "gauge"

        if cls._looks_scatter(rows, label_key, numeric_keys):
            return "scatter"

        if cls._looks_combo(numeric_keys):
            return "combo" if cls._looks_temporal(rows, label_key) else "grouped_bar"

        if cls._looks_histogram(rows, numeric_keys):
            return "histogram"

        if cls._looks_temporal(rows, label_key):
            return "line" if len(numeric_keys) <= 1 else "multi_line"

        if len(numeric_keys) >= 2 and cls._message_mentions_stacked(message):
            return "stacked_bar"

        if len(numeric_keys) >= 2:
            return "grouped_bar"

        if cls._looks_participation(rows, numeric_keys) and 3 <= len(rows) <= 10:
            return "donut"

        labels = [str(row.get(label_key) or "") for row in rows]

        if len(rows) > 6 or any(len(label) > 14 for label in labels):
            return "horizontal_bar"

        return "bar"

    @classmethod
    def _resolve_from_message(cls, message: str) -> str | None:
        if any(token in message for token in ("rosca", "donut", "particip", "pizza", "fatia")):
            if "barra horizontal" in message or "horizontal" in message:
                return "horizontal_bar"

            return "donut"

        if any(token in message for token in _HORIZONTAL_HINTS):
            return "horizontal_bar"

        if any(token in message for token in ("linha", "linhas", "evolu", "série", "serie", "tendên")):
            return "line"

        if any(token in message for token in _STACKED_HINTS):
            return "stacked_bar"

        if any(token in message for token in ("agrupad", "compar", "meta", "versus", " vs ")):
            return "grouped_bar"

        if "área" in message or "area" in message:
            return "area"

        if any(token in message for token in ("dispers", "scatter", "correla", "correlação")):
            return "scatter"

        if any(token in message for token in ("histograma", "distribui", "frequencia", "frequência")):
            return "histogram"

        if any(token in message for token in ("velocimetro", "velocímetro", "gauge", "medidor")):
            return "gauge"

        if any(token in message for token in ("combo", "combinado")):
            return "combo"

        if any(token in message for token in ("heatmap", "mapa de calor", "mapa calor", "matriz")):
            return "heatmap"

        return None

    @classmethod
    def _looks_heatmap_matrix(
        cls,
        rows: list[dict[str, Any]],
        string_keys: list[str],
        numeric_keys: list[str],
    ) -> bool:
        if len(rows) < 4 or len(string_keys) < 2 or len(numeric_keys) != 1:
            return False

        if len(rows) > 144:
            return False

        x_key, y_key = cls._pick_heatmap_axes(string_keys, rows)
        x_count = len({str(row.get(x_key) or "") for row in rows})
        y_count = len({str(row.get(y_key) or "") for row in rows})

        if x_count < 2 or y_count < 2:
            return False

        if x_count > 16 or y_count > 16:
            return False

        return x_count * y_count >= len(rows) * 0.5

    @classmethod
    def _pick_heatmap_axes(
        cls,
        string_keys: list[str],
        rows: list[dict[str, Any]],
    ) -> tuple[str, str]:
        cardinalities = {
            key: len({str(row.get(key) or "") for row in rows})
            for key in string_keys
        }
        ordered = sorted(string_keys, key=lambda key: cardinalities.get(key, 0))

        return ordered[-1], ordered[0]

    @classmethod
    def _message_mentions_stacked(cls, message: str) -> bool:
        return any(token in message for token in _STACKED_HINTS)

    @classmethod
    def _looks_temporal(cls, rows: list[dict[str, Any]], label_key: str) -> bool:
        label_token = str(label_key or "").lower()

        if any(token in label_token for token in _TEMPORAL_LABEL_TOKENS):
            return True

        samples = [str(row.get(label_key) or "").strip() for row in rows[:8] if row.get(label_key)]

        if not samples:
            return False

        date_like = sum(
            1
            for value in samples
            if re.search(r"\d{4}", value)
            or re.search(r"\d{1,2}/\d{1,2}", value)
            or re.search(r"\d{4}-\d{2}", value)
        )

        return date_like >= max(2, len(samples) // 2)

    @classmethod
    def _looks_participation(cls, rows: list[dict[str, Any]], numeric_keys: list[str]) -> bool:
        if len(numeric_keys) != 1:
            return False

        key = numeric_keys[0]
        values: list[float] = []

        for row in rows:
            raw = row.get(key)

            if isinstance(raw, (int, float)):
                values.append(float(raw))

        if len(values) < 3:
            return False

        total = sum(values)

        if total <= 0:
            return False

        if 95 <= total <= 105 or 0.95 <= total <= 1.05:
            return True

        key_lower = key.lower()

        return any(token in key_lower for token in _PARTICIPATION_HINTS)

    @classmethod
    def _looks_gauge(cls, rows: list[dict[str, Any]], numeric_keys: list[str]) -> bool:
        if len(rows) != 1 or not numeric_keys:
            return False

        lowered = [key.lower() for key in numeric_keys]

        has_target = any(
            any(token in key for token in _COMBO_TARGET_KEYS)
            for key in lowered
        )
        has_value = any(
            any(token in key for token in _COMBO_VALUE_KEYS)
            for key in lowered
        )

        return has_target and has_value

    @classmethod
    def _looks_scatter(
        cls,
        rows: list[dict[str, Any]],
        label_key: str,
        numeric_keys: list[str],
    ) -> bool:
        if len(numeric_keys) < 2 or len(rows) < 3:
            return False

        if cls._looks_temporal(rows, label_key):
            return False

        label_token = str(label_key or "").lower()

        if any(token in label_token for token in _TEMPORAL_LABEL_TOKENS):
            return False

        return True

    @classmethod
    def _looks_combo(cls, numeric_keys: list[str]) -> bool:
        if len(numeric_keys) < 2:
            return False

        lowered = [key.lower() for key in numeric_keys]

        has_target = any(
            any(token in key for token in _COMBO_TARGET_KEYS)
            for key in lowered
        )
        has_value = any(
            any(token in key for token in _COMBO_VALUE_KEYS)
            for key in lowered
        )

        return has_target and has_value

    @classmethod
    def _looks_histogram(cls, rows: list[dict[str, Any]], numeric_keys: list[str]) -> bool:
        return len(numeric_keys) == 1 and len(rows) >= 8
