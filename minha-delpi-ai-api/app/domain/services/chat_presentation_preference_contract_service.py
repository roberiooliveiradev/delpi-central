"""Contrato canônico de preferência de apresentação (requestedPresentation).

Fonte única alinhada a openapi_tool_routing.json — evita allowlists divergentes.
"""

from __future__ import annotations

from typing import Any

# Keep in sync with openapi_tool_routing.json planner.schema.requestedPresentation.enum
REQUESTED_PRESENTATION_TOKENS = frozenset(
    {
        "auto",
        "kpi",
        "table",
        "chart",
        "text",
        "tree",
        "canvas",
        "dashboard",
        "topics",
        "line_chart",
        "bar_chart",
        "horizontal_bar",
        "donut",
        "checklist",
    }
)

# Tokens that may override session/tool presentation (excludes auto).
EXPLICIT_PRESENTATION_TOKENS = frozenset(
    token for token in REQUESTED_PRESENTATION_TOKENS if token != "auto"
)

SESSION_RESPONSE_FORMAT_TOKENS = frozenset(
    {
        "kpi",
        "table",
        "text",
        "tree",
        "chart",
        "topics",
        "canvas",
        "dashboard",
    }
)


class ChatPresentationPreferenceContractService:
    @classmethod
    def normalize(cls, value: Any) -> str | None:
        token = str(value or "").strip().lower()
        if not token or token in {"none", "null"}:
            return None
        if token in REQUESTED_PRESENTATION_TOKENS:
            return token
        aliases = {
            "texto": "text",
            "tabela": "table",
            "grafico": "chart",
            "gráfico": "chart",
            "arvore": "tree",
            "árvore": "tree",
            "lousa": "canvas",
        }
        mapped = aliases.get(token)
        return mapped if mapped in REQUESTED_PRESENTATION_TOKENS else None

    @classmethod
    def normalize_from_message(cls, message: str) -> str | None:
        from app.domain.services.chat_presentation_user_format_preference_service import (
            ChatPresentationUserFormatPreferenceService,
        )

        preferred = ChatPresentationUserFormatPreferenceService.normalize_from_message(
            None,
            message,
        )
        return cls.normalize(preferred)

    @classmethod
    def as_session_response_format(cls, value: Any) -> str | None:
        token = cls.normalize(value)
        if token is None or token == "auto":
            return None
        if token in SESSION_RESPONSE_FORMAT_TOKENS:
            return token
        if token in {"line_chart", "bar_chart", "horizontal_bar", "donut"}:
            return "chart"
        return None

    @classmethod
    def is_explicit(cls, value: Any) -> bool:
        token = cls.normalize(value)
        return token is not None and token in EXPLICIT_PRESENTATION_TOKENS
