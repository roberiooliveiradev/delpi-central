"""Explicação textual de gráficos — Playbook 09 Fase 4 (inline, sem LLM)."""

from __future__ import annotations

import statistics
from typing import Any

from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)

_CHART_TYPE_LABELS = {
    "bar": "gráfico de barras",
    "horizontal_bar": "gráfico de barras horizontais",
    "line": "gráfico de linhas",
    "multi_line": "gráfico de linhas",
    "area": "gráfico de área",
    "donut": "gráfico de rosca",
    "pie": "gráfico de pizza",
    "grouped_bar": "gráfico de barras agrupadas",
    "stacked_bar": "gráfico de barras empilhadas",
    "combo": "gráfico combinado (barras e linha)",
    "scatter": "gráfico de dispersão",
    "histogram": "histograma",
    "gauge": "indicador tipo velocímetro",
    "heatmap": "mapa de calor",
}

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
    ) -> str:
        if not isinstance(presentation, dict) or presentation.get("type") != "chart":
            return ""

        data = presentation.get("data") or []

        if not isinstance(data, list) or not data:
            return "Não há pontos suficientes para explicar este gráfico."

        rows = [row for row in data if isinstance(row, dict)]

        if not rows:
            return "Não há pontos suficientes para explicar este gráfico."

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
        parts.append(cls._how_to_read(chart_type, x_axis, y_axis, rows))

        highlight = cls._highlights(chart_type, rows, x_axis, y_axis)

        if highlight:
            parts.append(highlight)

        parts.append(
            "Use os seletores acima para trocar eixo, filtrar por categoria ou alternar o tipo de gráfico — "
            "sem precisar enviar nova pergunta."
        )

        return "\n\n".join(part for part in parts if part)

    @classmethod
    def _label(cls, key: str) -> str:
        return cls._label_service.label_for(key) or key.replace("_", " ").strip()

    @classmethod
    def _intro(cls, chart_type: str, selected: str, reason: str, row_count: int) -> str:
        chart_label = _CHART_TYPE_LABELS.get(chart_type, "gráfico")

        if reason:
            return (
                f"Este {chart_label} reúne {row_count} ponto(s) e foi escolhido porque {reason}."
            )

        if selected:
            return f"Este {chart_label} reúne {row_count} ponto(s) (formato «{selected}»)."

        return f"Este {chart_label} reúne {row_count} ponto(s) dos dados consultados."

    @classmethod
    def _how_to_read(
        cls,
        chart_type: str,
        x_axis: str,
        y_axis: str,
        rows: list[dict[str, Any]],
    ) -> str:
        if chart_type == "scatter" and x_axis and y_axis:
            return (
                f"No eixo horizontal (X) está «{cls._label(x_axis)}»; no vertical (Y), «{cls._label(y_axis)}». "
                "Cada ponto é um registro — procure agrupamentos e valores fora do padrão."
            )

        if chart_type in {"line", "multi_line", "area"} and x_axis and y_axis:
            return (
                f"O eixo horizontal mostra «{cls._label(x_axis)}» (período ou sequência); "
                f"o vertical, «{cls._label(y_axis)}». Siga a linha da esquerda para a direita para ver a evolução."
            )

        if chart_type in {"donut", "pie"} and y_axis:
            category_key = x_axis or cls._guess_category_key(rows, {y_axis})

            return (
                f"Cada fatia é «{cls._label(category_key)}»; o tamanho reflete «{cls._label(y_axis)}» "
                "em relação ao total."
            )

        if chart_type in {"horizontal_bar", "bar", "histogram"} and y_axis:
            category_key = x_axis or cls._guess_category_key(rows, {y_axis})

            return (
                f"As categorias em «{cls._label(category_key)}» são comparadas pelo valor de "
                f"«{cls._label(y_axis)}» — barras maiores indicam valores mais altos."
            )

        if chart_type == "gauge" and y_axis:
            return f"O medidor destaca «{cls._label(y_axis)}» em relação à meta ou ao intervalo esperado."

        if x_axis and y_axis:
            return (
                f"Compare «{cls._label(x_axis)}» (categorias ou eixo X) com «{cls._label(y_axis)}» (valores)."
            )

        return "Posicione o cursor sobre barras, pontos ou fatias para ver o valor exato de cada item."

    @classmethod
    def _highlights(
        cls,
        chart_type: str,
        rows: list[dict[str, Any]],
        x_axis: str,
        y_axis: str,
    ) -> str:
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
        leader_label = str(leader_row.get(category_key) or "o maior valor").strip()
        laggard_label = str(laggard_row.get(category_key) or "o menor valor").strip()
        leader_value = leader_row.get(y_axis)
        laggard_value = laggard_row.get(y_axis)

        y_label = cls._label(y_axis)
        is_efficiency = any(token in y_axis.lower() for token in _EFFICIENCY_TOKENS)

        if is_efficiency:
            return (
                f"Em «{y_label}», o destaque é {leader_label} ({cls._format_value(leader_value)}%) "
                f"e o menor registro é {laggard_label} ({cls._format_value(laggard_value)}%). "
                "Valores acima de 100% indicam produção acima do tempo previsto."
            )

        if chart_type == "scatter":
            avg_x = cls._average_for_key(rows, x_axis) if x_axis else None
            avg_y = statistics.fmean(values)

            extra = ""

            if avg_x is not None and x_axis:
                extra = f" A média de «{cls._label(x_axis)}» é {cls._format_value(avg_x)};"

            return (
                f"Em «{y_label}», o ponto mais alto é {leader_label} ({cls._format_value(leader_value)}) "
                f"e o mais baixo é {laggard_label} ({cls._format_value(laggard_value)}).{extra} "
                f"A média de «{y_label}» é {cls._format_value(avg_y)}."
            )

        if len(values) >= 2:
            return (
                f"O maior valor de «{y_label}» é {leader_label} ({cls._format_value(leader_value)}); "
                f"o menor, {laggard_label} ({cls._format_value(laggard_value)}). "
                f"Média: {cls._format_value(statistics.fmean(values))}."
            )

        return (
            f"O valor de «{y_label}» em {leader_label} é {cls._format_value(leader_value)}."
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
