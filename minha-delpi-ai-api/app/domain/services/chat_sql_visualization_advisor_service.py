"""Recomendação de visualização para resultados SQL — Playbook §40."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class ChatSqlVisualizationAdvisorService:
    @classmethod
    def recommend(
        cls,
        *,
        message: str | None = None,
        mode: str | None = None,
        result_analysis: dict[str, Any] | None = None,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        resolved_columns = columns or []

        if isinstance(result_analysis, dict) and not resolved_columns:
            raw = result_analysis.get("columns")

            if isinstance(raw, list):
                resolved_columns = [str(item) for item in raw if str(item).strip()]

        chart_type = cls._resolve_chart_type(
            normalized=normalized,
            mode=mode,
            result_analysis=result_analysis,
            columns=resolved_columns,
        )

        return {
            "chartType": chart_type,
            "presentationType": cls._presentation_for_chart(chart_type),
            "reason": cls._reason_for_chart(chart_type),
            "suggestedLabel": cls._label_for_chart(chart_type),
        }

    @classmethod
    def _resolve_chart_type(
        cls,
        *,
        normalized: str,
        mode: str | None,
        result_analysis: dict[str, Any] | None,
        columns: list[str],
    ) -> str:
        if mode == "visualize":
            if "tabela" in normalized or "table" in normalized:
                return "table"

            if "lousa" in normalized or "canvas" in normalized:
                return "canvas"

        if any(token in normalized for token in ("ranking", "top ", "maior", "menor")):
            return "horizontal_bar"

        if any(
            token in normalized
            for token in ("particip", "percentual", "percent", "fatia", "rosca", "pizza")
        ):
            return "donut"

        if any(token in normalized for token in ("compar", "versus", "vs ", " lado a lado")):
            return "grouped_bar"

        if any(token in normalized for token in ("mes", "mês", "dia", "semana", "ano", "periodo", "período", "evoluc", "evoluç")):
            return "line"

        if isinstance(result_analysis, dict):
            if result_analysis.get("isEmpty"):
                return "table"

            row_count = int(result_analysis.get("rowCount") or 0)

            if row_count == 1:
                return "kpi"

            if row_count <= 12 and cls._has_numeric_columns(columns):
                return "horizontal_bar"

        column_text = " ".join(columns).lower()

        if any(token in column_text for token in ("data", "mes", "mês", "periodo", "período", "dt_")):
            return "line"

        if any(token in column_text for token in ("rank", "posicao", "posição", "ordem")):
            return "horizontal_bar"

        return "table"

    @classmethod
    def _has_numeric_columns(cls, columns: list[str]) -> bool:
        hints = ("valor", "total", "qtd", "quant", "amount", "fatur", "preco", "preço", "saldo")

        joined = " ".join(columns).lower()

        return any(hint in joined for hint in hints)

    @classmethod
    def _presentation_for_chart(cls, chart_type: str) -> str:
        mapping = {
            "horizontal_bar": "chart",
            "grouped_bar": "chart",
            "line": "chart",
            "donut": "chart",
            "kpi": "kpi",
            "table": "table",
            "canvas": "canvas",
        }

        return mapping.get(chart_type, "table")

    @classmethod
    def _reason_for_chart(cls, chart_type: str) -> str:
        reasons = {
            "horizontal_bar": "Ranking ou comparação de categorias — barras horizontais facilitam leitura.",
            "grouped_bar": "Comparação entre grupos — barras agrupadas destacam diferenças.",
            "line": "Série temporal — linha mostra evolução ao longo do tempo.",
            "donut": "Participação relativa — rosca evidencia fatias do total.",
            "kpi": "Indicador único — KPI destaca o valor principal.",
            "table": "Detalhamento — tabela preserva todas as colunas.",
            "canvas": "Relatório analítico — lousa organiza blocos e gráficos.",
        }

        return reasons.get(chart_type, reasons["table"])

    @classmethod
    def _label_for_chart(cls, chart_type: str) -> str:
        labels = {
            "horizontal_bar": "Ver em gráfico de barras",
            "grouped_bar": "Comparar em barras",
            "line": "Ver evolução em linha",
            "donut": "Ver participação",
            "kpi": "Ver como KPI",
            "table": "Ver em tabela",
            "canvas": "Colocar na lousa",
        }

        return labels.get(chart_type, "Gerar gráfico")
