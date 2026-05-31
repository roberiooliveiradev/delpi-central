"""Seleção automática de chartType — Playbook ampliação de gráficos, Fase 2."""

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

        return None

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
