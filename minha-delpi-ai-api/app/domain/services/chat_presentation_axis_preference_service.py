"""Preferência de eixos X/Y para gráficos — Playbook 09."""

from __future__ import annotations

import re
from typing import Any

_Y_PRIORITY = (
    "eficiencia",
    "eficência",
    "efficiency",
    "percentual",
    "percent",
    "pct",
    "yield",
    "taxa",
    "margem",
)
_Y_DEPRIORITY = (
    "tempo",
    "hora",
    "previsto",
    "real",
    "duration",
    "minuto",
    "segundo",
)
_X_SCATTER_PRIORITY = ("qtd", "quantidade", "qty", "quantity", "apontad")
_X_CATEGORY_PRIORITY = (
    "operador",
    "nome",
    "produto",
    "cliente",
    "fornecedor",
    "filial",
    "centro",
    "op",
    "ov",
)
_MESSAGE_HINTS = {
    "eficiencia": _Y_PRIORITY,
    "eficiência": _Y_PRIORITY,
    "fabril": _Y_PRIORITY,
    "produtividade": _Y_PRIORITY,
}


class ChatPresentationAxisPreferenceService:
    @classmethod
    def resolve(
        cls,
        *,
        rows: list[dict[str, Any]],
        chart_type: str,
        label_key: str,
        numeric_keys: list[str],
        user_message: str | None = None,
    ) -> dict[str, Any]:
        safe_rows = [row for row in rows if isinstance(row, dict)]
        sample = safe_rows[0] if safe_rows else {}

        numeric_columns = cls.list_numeric_keys(sample)
        category_columns = cls.list_category_keys(sample, numeric_columns)

        if not numeric_columns:
            return {
                "xAxis": label_key,
                "yAxis": [],
                "numericColumns": [],
                "categoryColumns": category_columns,
            }

        message = re.sub(r"\s+", " ", str(user_message or "").strip().lower())
        hint_tokens = cls._hint_tokens(message)

        y_axis = cls._pick_y_axis(numeric_columns, hint_tokens=hint_tokens)
        token = str(chart_type or "bar").strip().lower()

        if token == "scatter" and len(numeric_columns) >= 2:
            x_axis = cls._pick_scatter_x(numeric_columns, y_axis=y_axis, hint_tokens=hint_tokens)

            return {
                "xAxis": x_axis,
                "yAxis": [y_axis],
                "numericColumns": numeric_columns,
                "categoryColumns": category_columns,
            }

        category_axis = cls._pick_category_axis(
            category_columns,
            label_key=label_key,
            hint_tokens=hint_tokens,
        )

        remaining = [key for key in numeric_columns if key != y_axis]

        return {
            "xAxis": category_axis,
            "yAxis": [y_axis, *remaining[:2]],
            "numericColumns": numeric_columns,
            "categoryColumns": category_columns,
        }

    @classmethod
    def apply_to_chart_config(
        cls,
        presentation: dict[str, Any],
        *,
        user_message: str | None = None,
    ) -> None:
        if presentation.get("type") != "chart":
            return

        data = presentation.get("data") or []

        if not isinstance(data, list) or not data:
            return

        config = presentation.get("config")

        if not isinstance(config, dict):
            config = {}
            presentation["config"] = config

        label_key = str(config.get("xAxis") or "")
        y_axis = config.get("yAxis")
        numeric_keys = (
            list(y_axis)
            if isinstance(y_axis, list)
            else [str(y_axis)]
            if isinstance(y_axis, str) and y_axis
            else cls.list_numeric_keys(data[0])
        )

        resolved = cls.resolve(
            rows=data,
            chart_type=str(presentation.get("chartType") or "bar"),
            label_key=label_key,
            numeric_keys=numeric_keys,
            user_message=user_message,
        )

        config["xAxis"] = resolved["xAxis"]
        config["yAxis"] = resolved["yAxis"]
        config["numericColumns"] = resolved["numericColumns"]
        config["categoryColumns"] = resolved["categoryColumns"]

    @classmethod
    def list_numeric_keys(cls, sample: dict[str, Any]) -> list[str]:
        return [
            key
            for key, value in sample.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        ]

    @classmethod
    def list_category_keys(
        cls,
        sample: dict[str, Any],
        numeric_keys: list[str] | None = None,
    ) -> list[str]:
        blocked = set(numeric_keys or [])

        return [
            key
            for key, value in sample.items()
            if key not in blocked and isinstance(value, str) and str(value).strip()
        ]

    @classmethod
    def _hint_tokens(cls, message: str) -> tuple[str, ...]:
        tokens: list[str] = []

        for hint, priorities in _MESSAGE_HINTS.items():
            if hint in message:
                tokens.extend(priorities)

        return tuple(tokens)

    @classmethod
    def _score_key(cls, key: str, *, priorities: tuple[str, ...], depriorities: tuple[str, ...]) -> int:
        lowered = str(key or "").lower()
        score = 0

        for index, token in enumerate(priorities):
            if token in lowered:
                score += 100 - index

        for token in depriorities:
            if token in lowered:
                score -= 40

        return score

    @classmethod
    def _pick_y_axis(cls, numeric_keys: list[str], *, hint_tokens: tuple[str, ...]) -> str:
        priorities = hint_tokens + _Y_PRIORITY

        return max(
            numeric_keys,
            key=lambda key: cls._score_key(
                key,
                priorities=priorities,
                depriorities=_Y_DEPRIORITY,
            ),
        )

    @classmethod
    def _pick_scatter_x(
        cls,
        numeric_keys: list[str],
        *,
        y_axis: str,
        hint_tokens: tuple[str, ...],
    ) -> str:
        candidates = [key for key in numeric_keys if key != y_axis]

        if not candidates:
            return y_axis

        priorities = hint_tokens + _X_SCATTER_PRIORITY

        return max(
            candidates,
            key=lambda key: cls._score_key(
                key,
                priorities=priorities,
                depriorities=_Y_DEPRIORITY + (y_axis,),
            ),
        )

    @classmethod
    def _pick_category_axis(
        cls,
        category_columns: list[str],
        *,
        label_key: str,
        hint_tokens: tuple[str, ...],
    ) -> str:
        if not category_columns:
            return label_key or "name"

        return max(
            category_columns,
            key=lambda key: cls._score_key(
                key,
                priorities=hint_tokens + _X_CATEGORY_PRIORITY,
                depriorities=(),
            ),
        )
