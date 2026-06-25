"""Tipos — especialista SQL avançado."""

from __future__ import annotations

from typing import Any, Literal

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

SqlSpecialistMode = Literal[
    "create",
    "review",
    "explain",
    "optimize",
    "execute",
    "schema_explore",
    "incremental_edit",
    "analyze_result",
    "visualize",
    "none",
]

_MODE_ORDER: tuple[SqlSpecialistMode, ...] = (
    "review",
    "explain",
    "optimize",
    "schema_explore",
    "analyze_result",
    "visualize",
)


def _interactivity_content() -> dict[str, Any]:
    return ChatAssistantContentService.load_bundle("interactivity")
