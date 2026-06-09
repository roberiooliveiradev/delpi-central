"""Recomendações automáticas de formato — Playbook 09 Fase 5."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_presentation_data_shape_analyzer import (
    ChatPresentationDataShapeAnalyzer,
)

_CHART_SELECTED = frozenset(
    {
        "chart",
        "line_chart",
        "area_chart",
        "bar_chart",
        "horizontal_bar",
        "donut",
        "grouped_bar",
        "stacked_bar",
        "combo_chart",
        "histogram",
        "heatmap",
        "gauge",
        "scatter",
    }
)

class ChatPresentationRecommendationService:
    @classmethod
    def _view_labels(cls) -> dict[str, str]:
        return ChatAssistantContentService.get_mapping(
            "presenter_content",
            "presentationRecommendation",
            "viewLabels",
        )

    @classmethod
    def _view_queries(cls) -> dict[str, str]:
        return ChatAssistantContentService.get_mapping(
            "presenter_content",
            "presentationRecommendation",
            "viewQueries",
        )

    @classmethod
    def _efficiency_hints(cls) -> tuple[str, ...]:
        return tuple(
            ChatAssistantContentService.list(
                "presenter_content",
                "presentationRecommendation",
                "efficiencyHints",
            )
        )

    @classmethod
    def build(
        cls,
        *,
        decision: dict[str, Any] | None,
        user_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        if not isinstance(decision, dict):
            return []

        selected = str(decision.get("selected") or "").strip().lower()
        available = {
            str(view or "").strip().lower()
            for view in (decision.get("availableViews") or [])
            if str(view or "").strip()
        }

        if not selected or not available:
            return []

        rows = cls._rows_from_metadata(metadata)
        shape = decision.get("dataShape")

        if isinstance(shape, dict) and shape.get("rows"):
            ideal = ChatPresentationDataShapeAnalyzer.analyze(rows=rows).get("recommended")
        else:
            ideal = ChatPresentationDataShapeAnalyzer.analyze(rows=rows).get("recommended")

        ideal = str(ideal or "").strip().lower()
        message = re.sub(r"\s+", " ", str(user_message or "").strip().lower())

        output: list[dict[str, str]] = []
        seen: set[str] = set()

        def add(view: str, reason: str) -> None:
            token = str(view or "").strip().lower()

            if not token or token == selected or token in seen:
                return

            if not cls._view_available(token, available):
                return

            label = cls._view_labels().get(token, f"Ver como {token}")

            output.append(
                {
                    "view": token,
                    "label": label,
                    "reason": reason,
                    "query": cls._view_queries().get(token, f"mostre em {token}"),
                }
            )
            seen.add(token)

        if ideal and ideal != selected:
            add(ideal, cls._reason_for_view(ideal, decision))

        if message and any(hint in message for hint in cls._efficiency_hints()):
            if selected in {"scatter", "chart", "bar_chart"}:
                add(
                    "horizontal_bar",
                    "pergunta sobre eficiência — ranking por operador ou centro costuma ser mais legível",
                )

            if selected == "table" and ideal in {"", "table", "horizontal_bar"}:
                add(
                    "horizontal_bar",
                    "eficiência fabril fica mais clara em barras por operador ou centro",
                )

        if selected == "table" and "line_chart" in available:
            shape_dict = shape if isinstance(shape, dict) else {}

            if shape_dict.get("hasDate") and shape_dict.get("hasNumeric"):
                add("line_chart", "há datas e valores — a evolução em linha facilita a leitura")

        if selected in _CHART_SELECTED and "table" in available:
            row_count = int((shape or {}).get("rows") or len(rows) or 0)

            if row_count >= 8:
                add("table", "muitos pontos no gráfico — a tabela ajuda a conferir valores exatos")

        if (
            isinstance(metadata, dict)
            and isinstance(metadata.get("presentation"), dict)
            and metadata["presentation"].get("type") == "dashboard"
            and selected != "dashboard"
        ):
            add("dashboard", "há um painel consolidado com resumo e gráficos auxiliares")

        return output[:3]

    @classmethod
    def _rows_from_metadata(cls, metadata: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not isinstance(metadata, dict):
            return []

        for key in ("tablePresentation", "presentation", "chartPresentation"):
            block = metadata.get(key)

            if not isinstance(block, dict):
                continue

            if block.get("type") == "table":
                rows = block.get("rows") or []

                return [row for row in rows if isinstance(row, dict)]

            if block.get("type") == "chart":
                data = block.get("data") or []

                return [row for row in data if isinstance(row, dict)]

        return []

    @classmethod
    def _view_available(cls, view: str, available: set[str]) -> bool:
        if view in available:
            return True

        if view in {"line_chart", "area_chart", "bar_chart", "horizontal_bar", "donut", "scatter"}:
            return "chart" in available or view in available

        return False

    @classmethod
    def _reason_for_view(cls, view: str, decision: dict[str, Any]) -> str:
        shape = decision.get("dataShape") if isinstance(decision.get("dataShape"), dict) else {}
        fallback = str(decision.get("reason") or "").strip()

        if view == "line_chart" and shape.get("hasDate"):
            return "série temporal detectada nos dados"

        if view == "horizontal_bar" and int(shape.get("categoryCardinality") or 0) > 6:
            return "muitas categorias — ranking em barra horizontal"

        if view == "donut":
            return "poucas categorias com participação relativa"

        if view == "table" and fallback:
            return "alternativa em tabela para conferência detalhada"

        if view == "dashboard":
            return "visão consolidada disponível para este resultado"

        return fallback or "formato alternativo sugerido pelos dados"
