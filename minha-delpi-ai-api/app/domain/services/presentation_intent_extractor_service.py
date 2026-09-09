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

# Prefer axes inside parentheses: (produto × depósito/filial)
_PAREN_MATRIX = re.compile(
    r"\(([^()]{1,80}?[×x][^()]{1,80}?)\)",
    flags=re.IGNORECASE,
)

# Fallback matrix split — still used on the focused fragment, not the full narrative.
_COMPARE_SPLIT = re.compile(
    r"(.+?)\s*[×x]\s*(.+?)(?:\s+pela?\s+|\s+com\s+|\s+por\s+|\s*$)",
    flags=re.IGNORECASE,
)

_AXIS_SEP = re.compile(r"\s*[×x]\s*", flags=re.IGNORECASE)

_INSTRUCTIONAL_PREFIX = re.compile(
    r"^(?:"
    r"agora\s+)?"
    r"(?:"
    r"coloque\s+(?:isso|isto|esse\s+resultado)?\s*(?:em\s+(?:um\s+)?)?|"
    r"mostre\s+(?:isso\s+)?(?:em\s+(?:um\s+)?)?|"
    r"mostra\s+(?:isso\s+)?(?:em\s+(?:um\s+)?)?|"
    r"exiba\s+(?:isso\s+)?(?:em\s+(?:um\s+)?)?|"
    r"fa[cç]a\s+(?:um\s+)?|"
    r"transforme\s+(?:isso\s+)?(?:em\s+(?:um\s+)?)?|"
    r"gere\s+(?:um\s+)?"
    r")?",
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

        for part in cls._matrix_axis_parts(text):
            cleaned = cls._strip_view_noise(part)
            if cleaned and cleaned not in dimensions:
                dimensions.append(cleaned)

        # "pela produção" / "com qtd planejada"
        measure_match = re.search(
            r"(?:pela?|com|usando)\s+(?:a\s+)?([a-zà-ú0-9_./ ]{3,40})$",
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
    def _matrix_axis_parts(cls, text: str) -> list[str]:
        paren = _PAREN_MATRIX.search(text)
        if paren:
            return [part.strip() for part in _AXIS_SEP.split(paren.group(1)) if part.strip()]

        # Focus fragment: drop instructional / view noise before scanning ×.
        focused = cls._strip_view_noise(_INSTRUCTIONAL_PREFIX.sub("", text).strip())
        matrix = _COMPARE_SPLIT.search(focused) or _COMPARE_SPLIT.search(text)
        if not matrix:
            return []

        return [matrix.group(1).strip(), matrix.group(2).strip()]

    @classmethod
    def _strip_view_noise(cls, value: str) -> str:
        token = str(value or "").strip().lower()
        phrases = (
            "mapa de calor",
            "heatmap",
            "matriz de intensidade",
            "gráfico de barras",
            "grafico de barras",
            "gráfico de linha",
            "grafico de linha",
            "gráfico",
            "grafico",
            "tabela",
            "tons de azul",
            "agora coloque isso",
            "coloque isso",
            "coloque",
            "mostre",
            "mostra",
            "exiba",
            "faça",
            "faca",
            "transforme",
            "gere",
        )
        for item in phrases:
            token = token.replace(item, " ")
        token = re.sub(
            r"\b(em|da|do|das|dos|um|uma|o|a|os|as|azul|isso|isto|esse|esta|resultado)\b",
            " ",
            token,
        )
        token = token.replace("(", " ").replace(")", " ")
        return re.sub(r"\s+", " ", token).strip(" .,:;")
