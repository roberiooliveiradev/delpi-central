"""Extrai PresentationIntent da mensagem do usuário (conceitos, não keys)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.entities.presentation_spec import PresentationIntent
from app.domain.services.chat_presentation_preference_contract_service import (
    ChatPresentationPreferenceContractService,
)

_MARK_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("heatmap", ("mapa de calor", "heatmap", "matriz de intensidade")),
    ("line", ("gráfico de linha", "grafico de linha", "line chart", "série temporal", "serie temporal")),
    ("donut", ("rosca", "donut", "pizza", "pie")),
    ("horizontal_bar", ("barras horizontais", "h. barras", "horizontal bar")),
    ("bar", ("gráfico de barras", "grafico de barras", "barras", "bar chart")),
    ("scatter", ("dispersão", "dispersao", "scatter")),
    ("area", ("área", "area chart", "gráfico de área")),
)

_PALETTE_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("sequential-blue", ("azul", "tons de azul", "blue")),
    ("warm", ("quente", "laranja", "warm")),
    ("cool", ("frio", "ciano", "teal", "cool")),
    ("diverging-status", ("divergente", "status")),
    ("brand", ("marca", "brand", "corporativo")),
)

_DIM_PATTERNS = (
    (r"\bpor\s+([a-zà-ú0-9_ ]{2,40?}?)(?:\s+e\s+|\s*[×x]\s*|\s+com\s+|\s*$)", "dim"),
)

_COMPARE_SPLIT = re.compile(
    r"(.+?)\s*[×x]\s*(.+?)(?:\s+pela?\s+|\s+com\s+|\s+por\s+|\s*$)",
    flags=re.IGNORECASE,
)


class PresentationIntentExtractorService:
    @classmethod
    def extract(
        cls,
        message: str | None,
        *,
        requested_presentation: str | None = None,
    ) -> PresentationIntent:
        text = re.sub(r"\s+", " ", str(message or "").strip().lower())
        message_mark = cls._detect_mark(text, None)
        view = ChatPresentationPreferenceContractService.normalize(
            requested_presentation
        )
        if view is None:
            try:
                view = ChatPresentationPreferenceContractService.normalize_from_message(
                    message or ""
                )
            except Exception:
                view = None
        mark = message_mark or cls._detect_mark(text, view)
        palette = cls._detect_palette(text)
        dimensions, measure = cls._detect_concepts(text)

        # Map chart subtypes from requestedPresentation tokens.
        if view in {"line_chart", "bar_chart", "horizontal_bar", "donut"} and not mark:
            mark = {
                "line_chart": "line",
                "bar_chart": "bar",
                "horizontal_bar": "horizontal_bar",
                "donut": "donut",
            }.get(view)
            view = "chart"

        # Explicit visual mark in THIS message outranks sticky session format
        # (ex.: previous turn "lista" → table must not block "mapa de calor").
        if message_mark:
            mark = message_mark
            view = "chart"
        elif view in {"kpi", "table", "text", "tree", "canvas", "dashboard", "topics", "checklist"}:
            pass
        elif mark or view == "chart":
            view = "chart"

        return PresentationIntent(
            view=view,
            mark=mark,
            dimension_concepts=tuple(dimensions),
            measure_concept=measure,
            palette_family=palette,
            locale="pt-BR",
        )

    @classmethod
    def _detect_mark(cls, text: str, view: str | None) -> str | None:
        for mark, hints in _MARK_HINTS:
            if any(hint in text for hint in hints):
                return mark
        return None

    @classmethod
    def _detect_palette(cls, text: str) -> str | None:
        for family, hints in _PALETTE_HINTS:
            if any(hint in text for hint in hints):
                return family
        return None

    @classmethod
    def _detect_concepts(cls, text: str) -> tuple[list[str], str | None]:
        dimensions: list[str] = []
        measure: str | None = None

        matrix = _COMPARE_SPLIT.search(text)
        if matrix:
            left = matrix.group(1).strip()
            right = matrix.group(2).strip()
            for part in (left, right):
                cleaned = cls._strip_view_noise(part)
                if cleaned:
                    dimensions.append(cleaned)

        # "pela produção" / "com qtd planejada"
        measure_match = re.search(
            r"(?:pela?|com|usando)\s+(?:a\s+)?([a-zà-ú0-9_. ]{3,40})$",
            text,
        )
        if measure_match:
            measure = cls._strip_view_noise(measure_match.group(1))

        # "compare eficiência por máquina e turno"
        by_match = re.search(
            r"(?:compare|comparar|mostre|mostra|exiba)\s+(.+?)\s+por\s+(.+)$",
            text,
        )
        if by_match:
            measure = measure or cls._strip_view_noise(by_match.group(1))
            dims_raw = by_match.group(2)
            for chunk in re.split(r"\s+e\s+|\s*[×x,]\s*", dims_raw):
                cleaned = cls._strip_view_noise(chunk)
                if cleaned and cleaned not in dimensions:
                    dimensions.append(cleaned)

        return dimensions[:4], measure

    @classmethod
    def _strip_view_noise(cls, value: str) -> str:
        token = str(value or "").strip().lower()
        phrases = (
            "mapa de calor",
            "heatmap",
            "gráfico de barras",
            "grafico de barras",
            "gráfico de linha",
            "grafico de linha",
            "gráfico",
            "grafico",
            "tabela",
            "tons de azul",
        )
        for item in phrases:
            token = token.replace(item, " ")
        token = re.sub(
            r"\b(em|da|do|das|dos|um|uma|o|a|os|as|azul)\b",
            " ",
            token,
        )
        return re.sub(r"\s+", " ", token).strip(" .,:;")
