"""Explicação textual de gráficos — Playbook 09 Fase 4 (inline, sem LLM)."""

from __future__ import annotations

import statistics
from typing import Any

from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)
from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)

_EFFICIENCY_TOKENS = ("eficiencia", "eficiência", "efficiency", "percentual", "oee", "yield")


class ChatPresentationChartExplainService:
    _label_service = ExternalActionColumnLabelService()

    @classmethod
    def build(
        cls,
        *,
        presentation: dict[str, Any] | None,
        decision: dict[str, Any] | None = None,
        insight: str | None = None,
        path: str = "",
    ) -> str:
        vocab = ChatPresentationVocabularyService

        if not isinstance(presentation, dict) or presentation.get("type") != "chart":
            return ""

        data = presentation.get("data") or []

        if not isinstance(data, list) or not data:
            return vocab.chart_explain_text("insufficientData")

        rows = [row for row in data if isinstance(row, dict)]

        if not rows:
            return vocab.chart_explain_text("insufficientData")

        config = presentation.get("config") if isinstance(presentation.get("config"), dict) else {}
        chart_type = str(presentation.get("chartType") or config.get("recommendedChartType") or "bar").strip().lower()
        selected = str((decision or {}).get("selected") or "").strip().lower()
        reason = str((decision or {}).get("reason") or "").strip()

        x_axis = str(config.get("xAxis") or "").strip()
        y_axes = config.get("yAxis")

        if isinstance(y_axes, list):
            y_axis = str(y_axes[0] or "").strip() if y_axes else ""
        else:
            y_axis = str(y_axes or "").strip()

        parts: list[str] = []

        insight_text = str(insight or (decision or {}).get("insight") or "").strip()

        if insight_text:
            parts.append(insight_text)

        parts.append(cls._intro(chart_type, selected, reason, len(rows)))
        parts.append(cls._how_to_read(chart_type, x_axis, y_axis, rows, path=path))

        highlight = cls._highlights(chart_type, rows, x_axis, y_axis, path=path)

        if highlight:
            parts.append(highlight)

        parts.append(vocab.chart_explain_text("selectorHint"))

        return "\n\n".join(part for part in parts if part)

    @classmethod
    def _label(cls, key: str, *, path: str = "") -> str:
        return cls._label_service.label_for(key, path=path) or key.replace("_", " ").strip()

    @classmethod
    def _intro(cls, chart_type: str, selected: str, reason: str, row_count: int) -> str:
        vocab = ChatPresentationVocabularyService
        chart_label = vocab.chart_type_label(chart_type)

        if reason:
            return vocab.chart_explain_text(
                "introWithReason",
                chartLabel=chart_label,
                rowCount=row_count,
                reason=reason,
            )

        if selected:
            return vocab.chart_explain_text(
                "introWithSelected",
                chartLabel=chart_label,
                rowCount=row_count,
                selected=selected,
            )

        return vocab.chart_explain_text(
            "introDefault",
            chartLabel=chart_label,
            rowCount=row_count,
        )

    @classmethod
    def _how_to_read(
        cls,
        chart_type: str,
        x_axis: str,
        y_axis: str,
        rows: list[dict[str, Any]],
        *,
        path: str = "",
    ) -> str:
        vocab = ChatPresentationVocabularyService

        if chart_type == "scatter" and x_axis and y_axis:
            return vocab.chart_explain_text(
                "howToReadScatter",
                xLabel=cls._label(x_axis, path=path),
                yLabel=cls._label(y_axis, path=path),
            )

        if chart_type in {"line", "multi_line", "area"} and x_axis and y_axis:
            return vocab.chart_explain_text(
                "howToReadTemporal",
                xLabel=cls._label(x_axis, path=path),
                yLabel=cls._label(y_axis, path=path),
            )

        if chart_type in {"donut", "pie"} and y_axis:
            category_key = x_axis or cls._guess_category_key(rows, {y_axis})

            return vocab.chart_explain_text(
                "howToReadDonut",
                categoryLabel=cls._label(category_key, path=path),
                yLabel=cls._label(y_axis, path=path),
            )

        if chart_type in {"horizontal_bar", "bar", "histogram"} and y_axis:
            category_key = x_axis or cls._guess_category_key(rows, {y_axis})

            return vocab.chart_explain_text(
                "howToReadBar",
                categoryLabel=cls._label(category_key, path=path),
                yLabel=cls._label(y_axis, path=path),
            )

        if chart_type == "gauge" and y_axis:
            return vocab.chart_explain_text(
                "howToReadGauge",
                yLabel=cls._label(y_axis, path=path),
            )

        if x_axis and y_axis:
            return vocab.chart_explain_text(
                "howToReadGenericAxes",
                xLabel=cls._label(x_axis, path=path),
                yLabel=cls._label(y_axis, path=path),
            )

        return vocab.chart_explain_text("howToReadHover")

    @classmethod
    def _highlights(
        cls,
        chart_type: str,
        rows: list[dict[str, Any]],
        x_axis: str,
        y_axis: str,
        *,
        path: str = "",
    ) -> str:
        vocab = ChatPresentationVocabularyService

        if not y_axis:
            y_axis = cls._pick_numeric_key(rows[0])

        if not y_axis:
            return ""

        values = [
            float(row[y_axis])
            for row in rows
            if isinstance(row.get(y_axis), (int, float))
        ]

        if not values:
            return ""

        category_key = x_axis or cls._guess_category_key(rows, {y_axis})
        leader_row = max(
            rows,
            key=lambda row: float(row.get(y_axis) or 0)
            if isinstance(row.get(y_axis), (int, float))
            else 0,
        )
        laggard_row = min(
            rows,
            key=lambda row: float(row.get(y_axis) or 0)
            if isinstance(row.get(y_axis), (int, float))
            else 0,
        )
        leader_label = str(leader_row.get(category_key) or vocab.chart_explain_text("leaderFallback")).strip()
        laggard_label = str(laggard_row.get(category_key) or vocab.chart_explain_text("laggardFallback")).strip()
        leader_value = leader_row.get(y_axis)
        laggard_value = laggard_row.get(y_axis)

        y_label = cls._label(y_axis, path=path)
        is_efficiency = any(token in y_axis.lower() for token in _EFFICIENCY_TOKENS)

        if is_efficiency:
            return vocab.chart_explain_text(
                "highlightEfficiency",
                yLabel=y_label,
                leaderLabel=leader_label,
                leaderValue=cls._format_value(leader_value),
                laggardLabel=laggard_label,
                laggardValue=cls._format_value(laggard_value),
            )

        if chart_type == "scatter":
            avg_x = cls._average_for_key(rows, x_axis) if x_axis else None
            avg_y = statistics.fmean(values)
            avg_x_snippet = ""

            if avg_x is not None and x_axis:
                avg_x_snippet = vocab.chart_explain_text(
                    "highlightScatterAvgX",
                    xLabel=cls._label(x_axis, path=path),
                    avgX=cls._format_value(avg_x),
                )

            return vocab.chart_explain_text(
                "highlightScatter",
                yLabel=y_label,
                leaderLabel=leader_label,
                leaderValue=cls._format_value(leader_value),
                laggardLabel=laggard_label,
                laggardValue=cls._format_value(laggard_value),
                avgXSnippet=avg_x_snippet,
                avgY=cls._format_value(avg_y),
            )

        if len(values) >= 2:
            return vocab.chart_explain_text(
                "highlightRange",
                yLabel=y_label,
                leaderLabel=leader_label,
                leaderValue=cls._format_value(leader_value),
                laggardLabel=laggard_label,
                laggardValue=cls._format_value(laggard_value),
                avgY=cls._format_value(statistics.fmean(values)),
            )

        return vocab.chart_explain_text(
            "highlightSingle",
            yLabel=y_label,
            leaderLabel=leader_label,
            leaderValue=cls._format_value(leader_value),
        )

    @classmethod
    def _guess_category_key(cls, rows: list[dict[str, Any]], exclude: set[str]) -> str:
        sample = rows[0]

        for key, value in sample.items():
            if key in exclude:
                continue

            if isinstance(value, str) and value.strip():
                return str(key)

        return next((key for key in sample if key not in exclude), "name")

    @classmethod
    def _pick_numeric_key(cls, row: dict[str, Any]) -> str | None:
        for key, value in row.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return str(key)

        return None

    @classmethod
    def _average_for_key(cls, rows: list[dict[str, Any]], key: str) -> float | None:
        values = [
            float(row[key])
            for row in rows
            if key and isinstance(row.get(key), (int, float))
        ]

        if not values:
            return None

        return statistics.fmean(values)

    @classmethod
    def _format_value(cls, value: Any) -> str:
        if not isinstance(value, (int, float)):
            return str(value or "—")

        number = float(value)

        if abs(number - round(number)) < 0.01:
            return str(int(round(number)))

        return f"{number:.2f}".rstrip("0").rstrip(".")
